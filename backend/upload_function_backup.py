# Backup copy of the working upload function
@app.post("/uploadfile/")
async def upload_file(request: Request):
    """
    Upload and process multiple document files.
    Supports: PDF, Word, PowerPoint, Excel, and text files.
    """
    global vector_store
    
    print(f"========== UPLOAD DEBUG START ==========")
    print(f"Received file upload request")
    
    try:
        # Get files from multipart form
        form = await request.form()
        print("Form keys:", list(form.keys()))
        
        # Collect all files from the form
        uploaded_files = []
        
        # Method 1: Check for FastAPI UploadFile format (files)
        if 'files' in form:
            files_data = form.getlist('files')
            for file_data in files_data:
                if hasattr(file_data, 'filename') and file_data.filename:
                    uploaded_files.append(file_data)
        
        # Method 2: Check for old format (file_upload, file_upload_0, etc.)
        if not uploaded_files:
            # Check for single file upload (backward compatibility)
            single_file = form.get("file_upload")
            if single_file and hasattr(single_file, 'filename') and single_file.filename:
                uploaded_files.append(single_file)
            
            # Check for multiple file uploads (file_upload_0, file_upload_1, etc.)
            for key in form.keys():
                if key.startswith("file_upload_") and key != "file_upload":
                    file = form.get(key)
                    if file and hasattr(file, 'filename') and file.filename:
                        uploaded_files.append(file)
        
        print(f"Number of files: {len(uploaded_files)}")
        
        if not uploaded_files:
            print("ERROR: No files received")
            return {
                "status": "error",
                "message": "No files received"
            }
        
        # Process each file
        results = []
        total_chunks = 0
        total_pages = 0
        errors = []
        
        for i, file_upload in enumerate(uploaded_files):
            print(f"\n--- Processing file {i+1}/{len(uploaded_files)}: {file_upload.filename} ---")
            print(f"Content type: {file_upload.content_type}")
            print(f"File size: {file_upload.size if hasattr(file_upload, 'size') else 'Unknown'}")
            
            try:
                print(f"Step 1: Reading file content...")
                # Read the file content
                file_content = await file_upload.read()
                
                # Save to temporary file for inspection  
                import tempfile
                import os
                from pathlib import Path
                temp_file_path = None
                try:
                    # Use asyncio.to_thread for file operations to avoid blocking
                    async def create_temp_file_async(content, original_filename):
                        # Get the original file extension to preserve file type
                        original_extension = Path(original_filename).suffix if original_filename else '.txt'
                        
                        def _create_temp():
                            # Use a known temp directory to avoid getcwd() calls
                            import platform
                            if platform.system() == "Windows":
                                temp_dir = os.environ.get('TEMP', os.environ.get('TMP', 'C:\\temp'))
                            else:
                                temp_dir = '/tmp'
                            
                            # Ensure temp directory exists
                            os.makedirs(temp_dir, exist_ok=True)
                            
                            with tempfile.NamedTemporaryFile(delete=False, suffix=original_extension, dir=temp_dir) as temp_file:
                                temp_file.write(content)
                                return temp_file.name
                        
                        return await asyncio.to_thread(_create_temp)
                    
                    temp_file_path = await create_temp_file_async(file_content, file_upload.filename)
                    print(f"Temporary file saved at: {temp_file_path}")
                    
                    print(f"Step 2: Initializing vector store...")
                    if vector_store is None:
                        await initialize_vector_store()
                        print("Vector store initialized successfully")
                    
                    print(f"Step 3: Calling load_document with temp file...")
                    # Load and process the document using the async function directly
                    pages = await load_document(temp_file_path)
                    print(f"load_document returned {len(pages) if pages else 0} pages")
                    
                    if pages:
                        print(f"First page preview (first 200 chars): {str(pages[0])[:200] if pages[0] else 'Empty'}")
                    
                    pages = [str(page) for page in pages if isinstance(page, str)]
                    full_text = "\n\n".join(pages)
                    print(f"Full text length: {len(full_text)} characters")

                    print(f"Step 4: Splitting text into chunks...")
                    # Call the async function directly since it already handles threading
                    chunks = await split_text_into_chunks(full_text)
                    print(f"Created {len(chunks)} chunks")
                    print(f"========== CHUNK ANALYSIS ==========")
                    for j, chunk in enumerate(chunks[:3]):  # Show first 3 chunks as examples
                        print(f"Chunk {j+1} (length: {len(chunk)} chars): {chunk[:200]}...")
                    if len(chunks) > 3:
                        print(f"... and {len(chunks) - 3} more chunks")
                    print(f"========== END CHUNK ANALYSIS ==========")

                    if vector_store and chunks:
                        print(f"Step 5: Adding chunks to vector store...")
                        print(f"Vector store type: {type(vector_store).__name__}")
                        print(f"Number of chunks to add: {len(chunks)}")
                        
                        # Wrap vector store operations in asyncio.to_thread
                        await asyncio.to_thread(vector_store.add_texts, chunks)
                        print(f"✅ Successfully added {len(chunks)} chunks to vector store")
                    
                    results.append({
                        "filename": file_upload.filename,
                        "status": "success",
                        "pages": len(pages),
                        "chunks": len(chunks),
                        "content_preview": full_text[:200] if full_text else "No content"
                    })
                    
                    total_pages += len(pages)
                    total_chunks += len(chunks)
                    
                finally:
                    # Clean up temporary file using async thread wrapper
                    if temp_file_path:
                        await asyncio.to_thread(lambda: os.path.exists(temp_file_path) and os.unlink(temp_file_path))
                        print(f"Cleaned up temporary file: {temp_file_path}")
                        
            except Exception as e:
                print(f"========== UPLOAD ERROR FOR {file_upload.filename} ==========")
                print(f"Error type: {type(e).__name__}")
                print(f"Error message: {str(e)}")
                import traceback
                print(f"Full traceback:")
                traceback.print_exc()
                print(f"========== ERROR END ==========")
                
                error_msg = f"Error processing {file_upload.filename}: {str(e)}"
                errors.append(error_msg)
                results.append({
                    "filename": file_upload.filename,
                    "status": "error",
                    "message": str(e)
                })

        print("========== UPLOAD SUMMARY ==========")
        successful_files = [r for r in results if r["status"] == "success"]
        failed_files = [r for r in results if r["status"] == "error"]
        
        print(f"Total files processed: {len(uploaded_files)}")
        print(f"Successful: {len(successful_files)}")
        print(f"Failed: {len(failed_files)}")
        print(f"Total pages: {total_pages}")
        print(f"Total chunks: {total_chunks}")
        
        # Return comprehensive response
        if len(successful_files) == len(uploaded_files):
            # All files successful
            return {
                "status": "success",
                "message": f"Successfully processed {len(uploaded_files)} file(s)",
                "files_processed": len(uploaded_files),
                "total_pages": total_pages,
                "total_chunks": total_chunks,
                "results": results
            }
        elif len(successful_files) > 0:
            # Partial success
            return {
                "status": "partial_success",
                "message": f"Processed {len(successful_files)} out of {len(uploaded_files)} files successfully",
                "files_processed": len(successful_files),
                "files_failed": len(failed_files),
                "total_pages": total_pages,
                "total_chunks": total_chunks,
                "results": results,
                "errors": errors
            }
        else:
            # All files failed
            return {
                "status": "error",
                "message": f"Failed to process all {len(uploaded_files)} file(s)",
                "files_failed": len(failed_files),
                "results": results,
                "errors": errors
            }
            
    except Exception as e:
        print(f"========== UPLOAD ENDPOINT ERROR ==========")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"Full traceback:")
        traceback.print_exc()
        print(f"========== ENDPOINT ERROR END ==========")
        
        return {
            "status": "error",
            "message": f"Upload endpoint error: {str(e)}"
        }
