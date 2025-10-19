#!/bin/bash

# clear_storage.sh - Safely clear all DAA Chatbot storage data
# This script removes uploaded documents, database, and vector embeddings

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
STORAGE_DIR="$SCRIPT_DIR/storage"

echo ""
echo "========================================="
echo "  DAA Chatbot Storage Cleanup Utility"
echo "========================================="
echo ""

# Check if storage directories exist
if [ ! -d "$STORAGE_DIR" ]; then
    echo -e "${RED}Error: Storage directory not found at $STORAGE_DIR${NC}"
    exit 1
fi

# Show current storage usage
echo "Current storage usage:"
echo ""
if [ -d "$STORAGE_DIR/documents" ]; then
    DOCS_SIZE=$(du -sh "$STORAGE_DIR/documents" 2>/dev/null | cut -f1)
    echo "  Documents:  $DOCS_SIZE"
fi
if [ -d "$STORAGE_DIR/sqlite" ]; then
    DB_SIZE=$(du -sh "$STORAGE_DIR/sqlite" 2>/dev/null | cut -f1)
    echo "  SQLite DB:  $DB_SIZE"
fi
if [ -d "$STORAGE_DIR/chroma" ]; then
    CHROMA_SIZE=$(du -sh "$STORAGE_DIR/chroma" 2>/dev/null | cut -f1)
    echo "  ChromaDB:   $CHROMA_SIZE"
fi
echo ""

# Warning message
echo -e "${YELLOW}WARNING: This will permanently delete:${NC}"
echo "  • All uploaded documents"
echo "  • All chat conversations and history"
echo "  • All projects"
echo "  • All vector embeddings"
echo ""

# Ask for confirmation
read -p "Do you want to continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo -e "${GREEN}Operation cancelled.${NC}"
    exit 0
fi

# Ask about backup
echo ""
read -p "Create a backup before clearing? (yes/no): " BACKUP
if [ "$BACKUP" = "yes" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="$SCRIPT_DIR/storage_backup_$TIMESTAMP"

    echo ""
    echo "Creating backup..."
    mkdir -p "$BACKUP_DIR"

    if [ -d "$STORAGE_DIR/documents" ]; then
        cp -r "$STORAGE_DIR/documents" "$BACKUP_DIR/"
        echo "  ✓ Documents backed up"
    fi
    if [ -d "$STORAGE_DIR/sqlite" ]; then
        cp -r "$STORAGE_DIR/sqlite" "$BACKUP_DIR/"
        echo "  ✓ Database backed up"
    fi
    if [ -d "$STORAGE_DIR/chroma" ]; then
        cp -r "$STORAGE_DIR/chroma" "$BACKUP_DIR/"
        echo "  ✓ Vector store backed up"
    fi

    echo -e "${GREEN}Backup created at: $BACKUP_DIR${NC}"
    echo ""
fi

# Final confirmation
echo ""
echo -e "${RED}FINAL CONFIRMATION:${NC}"
read -p "Type 'DELETE' to proceed with clearing storage: " FINAL_CONFIRM
if [ "$FINAL_CONFIRM" != "DELETE" ]; then
    echo -e "${GREEN}Operation cancelled.${NC}"
    exit 0
fi

# Clear storage
echo ""
echo "Clearing storage..."

# Clear documents
if [ -d "$STORAGE_DIR/documents" ]; then
    rm -rf "$STORAGE_DIR/documents"/*
    echo "  ✓ Documents cleared"
fi

# Clear SQLite database
if [ -d "$STORAGE_DIR/sqlite" ]; then
    rm -rf "$STORAGE_DIR/sqlite"/*
    echo "  ✓ Database cleared"
fi

# Clear ChromaDB
if [ -d "$STORAGE_DIR/chroma" ]; then
    rm -rf "$STORAGE_DIR/chroma"/*
    echo "  ✓ Vector store cleared"
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Storage successfully cleared!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Restart the backend server if it's running"
echo "  2. The database will be automatically recreated"
echo "  3. Upload new documents and create new projects"
echo ""

if [ "$BACKUP" = "yes" ]; then
    echo -e "Your backup is saved at: ${GREEN}$BACKUP_DIR${NC}"
    echo ""
fi
