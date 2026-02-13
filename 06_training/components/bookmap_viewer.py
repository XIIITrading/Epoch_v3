"""
Epoch Trading System - Bookmap Viewer Component
Displays Bookmap snapshot images for trades.
"""

import streamlit as st
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def render_bookmap_viewer(
    bookmap_url: Optional[str],
    expanded: bool = False
):
    """
    Render Bookmap snapshot viewer.

    Args:
        bookmap_url: URL to Bookmap image (Supabase storage or external)
        expanded: Whether to expand by default
    """
    if not bookmap_url:
        return

    with st.expander("📊 Bookmap Snapshot", expanded=expanded):
        try:
            st.image(
                bookmap_url,
                caption="Bookmap snapshot at trade entry",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Failed to load Bookmap image: {e}")
            st.caption(f"URL: {bookmap_url}")


def render_bookmap_placeholder():
    """Render placeholder when no Bookmap is available."""
    with st.expander("📊 Bookmap Snapshot", expanded=False):
        st.info(
            "No Bookmap snapshot available for this trade.\n\n"
            "To add Bookmap snapshots:\n"
            "1. Capture screenshot during trade\n"
            "2. Upload to Supabase storage\n"
            "3. Add URL to trade_images table"
        )


def render_bookmap_upload(trade_id: str, supabase_client):
    """
    Render Bookmap upload interface.
    For future implementation.

    Args:
        trade_id: Trade ID to associate image with
        supabase_client: Supabase client for upload
    """
    with st.expander("📤 Upload Bookmap", expanded=False):
        uploaded_file = st.file_uploader(
            "Choose image file",
            type=['png', 'jpg', 'jpeg'],
            key=f"bookmap_upload_{trade_id}"
        )

        if uploaded_file is not None:
            st.image(uploaded_file, caption="Preview", use_container_width=True)

            if st.button("Upload", key=f"btn_upload_{trade_id}"):
                st.info("Upload functionality coming soon...")
                # TODO: Implement Supabase storage upload
                # 1. Upload to storage bucket
                # 2. Get public URL
                # 3. Insert into trade_images table
