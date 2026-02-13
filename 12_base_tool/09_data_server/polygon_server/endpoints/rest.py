"""
REST API endpoints for historical data
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
import pandas as pd
from datetime import datetime, timedelta
import json
from ..utils.json_encoder import polygon_json_dumps

# Import from parent polygon module
from ... import (
    PolygonDataManager,
    get_storage_statistics,
    get_rate_limit_status,
    get_latest_price,
    validate_ticker,
    validate_symbol_detailed,
    clear_cache
)

from ..models import (
    BarsRequest, BarsResponse, MultipleBarsRequest,
    SymbolValidationRequest, ErrorResponse
)
from ..config import config

router = APIRouter(prefix="/api/v1", tags=["market-data"])

# Initialize data manager
data_manager = PolygonDataManager()


@router.post("/bars")
async def get_bars(request: BarsRequest):
    """
    Get historical OHLCV bars for a symbol

    Returns pandas DataFrame converted to JSON format
    """
    try:
        # Set default dates if not provided
        current_time = datetime.now()

        if not request.end_date:
            if request.timeframe.value == "1sec":
                # For second data, use current time with seconds
                end_date = current_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                end_date = current_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            end_date = request.end_date

        if not request.start_date:
            # For second data, default to last 60 seconds
            if request.timeframe.value == "1sec":
                start = current_time - timedelta(seconds=60)
                start_date = start.strftime("%Y-%m-%d %H:%M:%S")
            else:
                start = current_time - timedelta(days=30)
                start_date = start.strftime("%Y-%m-%d %H:%M:%S")
        else:
            start_date = request.start_date

        # Apply smaller limit for second data to avoid huge responses
        if request.timeframe.value == "1sec":
            if not request.limit or request.limit > 60:
                request.limit = 60  # Max 60 second bars at a time

        # Log the request for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Fetching {request.symbol} {request.timeframe.value} from {start_date} to {end_date}, limit={request.limit}")

        # Fetch data
        df = data_manager.fetch_data(
            symbol=request.symbol,
            timeframe=request.timeframe.value,
            start_date=start_date,
            end_date=end_date,
            use_cache=request.use_cache,
            validate=request.validate
        )

        if df.empty:
            # Return empty result instead of 404 for second data
            if request.timeframe.value == "1sec":
                return {
                    "symbol": request.symbol,
                    "timeframe": request.timeframe.value,
                    "start_date": start_date,
                    "end_date": end_date,
                    "bar_count": 0,
                    "data": [],
                    "cached": request.use_cache,
                    "validation": None,
                    "message": "No second data available - your Polygon tier may not support second aggregates"
                }
            else:
                raise HTTPException(404, f"No data found for {request.symbol}")

        # Apply limit if specified
        if request.limit and len(df) > request.limit:
            df = df.tail(request.limit)

        # Convert to response format
        data_records = []
        for idx, row in df.iterrows():
            # Handle different timestamp formats
            if hasattr(idx, 'isoformat'):
                # It's a datetime object
                timestamp_str = idx.isoformat()
            elif isinstance(idx, (int, float)):
                # It's a Unix timestamp in milliseconds
                timestamp_str = datetime.fromtimestamp(idx / 1000).isoformat()
            else:
                # Try to convert to string
                timestamp_str = str(idx)

            record = {
                "timestamp": timestamp_str,
                "open": float(row["open"]) if pd.notna(row["open"]) else 0,
                "high": float(row["high"]) if pd.notna(row["high"]) else 0,
                "low": float(row["low"]) if pd.notna(row["low"]) else 0,
                "close": float(row["close"]) if pd.notna(row["close"]) else 0,
                "volume": int(row["volume"]) if pd.notna(row.get("volume", 0)) else 0,
                "vwap": float(row.get("vwap", 0)) if pd.notna(row.get("vwap", 0)) else 0,
                "transactions": int(row.get("transactions", 0)) if pd.notna(row.get("transactions", 0)) else 0
            }

            # Add bar timing info if available (useful for second bars)
            if 'bar_start' in row and pd.notna(row['bar_start']):
                if hasattr(row["bar_start"], 'isoformat'):
                    record["bar_start"] = row["bar_start"].isoformat()
                else:
                    record["bar_start"] = str(row["bar_start"])

            if 'bar_end' in row and pd.notna(row['bar_end']):
                if hasattr(row["bar_end"], 'isoformat'):
                    record["bar_end"] = row["bar_end"].isoformat()
                else:
                    record["bar_end"] = str(row["bar_end"])

            if 'bar_duration_sec' in row and pd.notna(row['bar_duration_sec']):
                record["bar_duration_sec"] = float(row["bar_duration_sec"])

            data_records.append(record)

        # Get validation results if requested
        validation = None
        if request.validate:
            try:
                validation = data_manager.validate_data(df, request.symbol, request.timeframe.value)
                # Convert validation to ensure no numpy types
                if validation:
                    validation = json.loads(polygon_json_dumps(validation))
            except Exception as e:
                logger.warning(f"Validation failed: {e}")
                validation = None

        # Format dates for response
        if not df.empty:
            # Handle the index dates properly
            if hasattr(df.index[0], 'strftime'):
                # For second data, include time in the response
                if request.timeframe.value == "1sec":
                    response_start_date = df.index[0].strftime("%Y-%m-%d %H:%M:%S")
                    response_end_date = df.index[-1].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    response_start_date = df.index[0].strftime("%Y-%m-%d")
                    response_end_date = df.index[-1].strftime("%Y-%m-%d")
            elif isinstance(df.index[0], (int, float)):
                # Unix timestamp in milliseconds
                start_dt = datetime.fromtimestamp(df.index[0] / 1000)
                end_dt = datetime.fromtimestamp(df.index[-1] / 1000)
                if request.timeframe.value == "1sec":
                    response_start_date = start_dt.strftime("%Y-%m-%d %H:%M:%S")
                    response_end_date = end_dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    response_start_date = start_dt.strftime("%Y-%m-%d")
                    response_end_date = end_dt.strftime("%Y-%m-%d")
            else:
                response_start_date = str(df.index[0])
                response_end_date = str(df.index[-1])
        else:
            response_start_date = start_date
            response_end_date = end_date

        return {
            "symbol": request.symbol,
            "timeframe": request.timeframe.value,
            "start_date": response_start_date,
            "end_date": response_end_date,
            "bar_count": len(df),
            "data": data_records,
            "cached": request.use_cache,
            "validation": validation
        }

    except HTTPException:
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_bars: {str(e)}")
        logger.error(traceback.format_exc())

        # Provide more specific error message
        error_msg = str(e)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            raise HTTPException(401, "Invalid Polygon API key")
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            raise HTTPException(403, "Your Polygon subscription tier may not support this timeframe")
        elif "404" in error_msg:
            raise HTTPException(404, f"Symbol {request.symbol} not found")
        elif "429" in error_msg:
            raise HTTPException(429, "Rate limit exceeded - please wait and try again")
        else:
            raise HTTPException(500, f"Error fetching data: {error_msg}")


@router.post("/bars/multiple")
async def get_multiple_bars(request: MultipleBarsRequest):
    """
    Get bars for multiple symbols
    """
    try:
        # Set default dates
        end_date = request.end_date or datetime.now()
        start_date = request.start_date or (datetime.now() - timedelta(days=30))
        
        if request.parallel:
            # Fetch in parallel
            results = data_manager.fetch_multiple_symbols(
                symbols=request.symbols,
                timeframe=request.timeframe.value,
                start_date=start_date,
                end_date=end_date
            )
        else:
            # Fetch sequentially
            results = {}
            for symbol in request.symbols:
                try:
                    df = data_manager.fetch_data(
                        symbol=symbol,
                        timeframe=request.timeframe.value,
                        start_date=start_date,
                        end_date=end_date
                    )
                    results[symbol] = df
                except Exception as e:
                    results[symbol] = {"error": str(e)}
        
        # Format response
        response = {}
        for symbol, data in results.items():
            if isinstance(data, pd.DataFrame) and not data.empty:
                response[symbol] = {
                    "success": True,
                    "bar_count": len(data),
                    "first_bar": data.index[0].isoformat(),
                    "last_bar": data.index[-1].isoformat()
                }
            else:
                response[symbol] = {
                    "success": False,
                    "error": data.get("error", "No data") if isinstance(data, dict) else "No data"
                }
        
        return response
        
    except Exception as e:
        raise HTTPException(500, f"Error fetching multiple symbols: {str(e)}")


@router.get("/latest/{symbol}")
async def get_latest_price_endpoint(symbol: str):  # Renamed to avoid conflict with imported function
    """Get latest price for a symbol"""
    try:
        price = get_latest_price(symbol.upper())
        if price is None:
            raise HTTPException(404, f"No price data for {symbol}")
            
        return {
            "symbol": symbol.upper(),
            "price": price,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Error getting latest price: {str(e)}")


@router.post("/validate")
async def validate_symbols(request: SymbolValidationRequest):
    """Validate if symbols are valid"""
    results = {}
    
    for symbol in request.symbols:
        try:
            if request.detailed:
                # Detailed validation
                validation = validate_symbol_detailed(symbol)
                results[symbol] = validation
            else:
                # Simple validation
                is_valid = validate_ticker(symbol)
                results[symbol] = {"valid": is_valid}
        except Exception as e:
            results[symbol] = {"valid": False, "error": str(e)}
    
    return results


@router.get("/search")
async def search_symbols(
    query: str = Query(..., description="Search query"),
    active_only: bool = Query(True, description="Only active symbols")
):
    """Search for symbols by name or ticker"""
    try:
        results = data_manager.search_symbols(query, active_only)
        return {"query": query, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(500, f"Search error: {str(e)}")


@router.get("/cache/stats")
async def get_cache_statistics():
    """Get cache statistics"""
    try:
        stats = get_storage_statistics()
        return stats
    except Exception as e:
        raise HTTPException(500, f"Error getting cache stats: {str(e)}")


@router.delete("/cache")
async def clear_cache_endpoint(  # Renamed to avoid conflict with imported function
    symbol: Optional[str] = Query(None, description="Clear specific symbol"),
    older_than_days: Optional[int] = Query(None, description="Clear data older than N days")
):
    """Clear cache data"""
    try:
        result = clear_cache(symbol=symbol, older_than_days=older_than_days)
        return result
    except Exception as e:
        raise HTTPException(500, f"Error clearing cache: {str(e)}")


@router.get("/rate-limit")
async def get_rate_limit():
    """Get current rate limit status"""
    try:
        status = get_rate_limit_status()
        return status
    except Exception as e:
        raise HTTPException(500, f"Error getting rate limit: {str(e)}")