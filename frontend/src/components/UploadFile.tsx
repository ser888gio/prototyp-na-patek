import axios from "axios";
import { ChangeEvent, useState } from "react";
import { MdDriveFolderUpload } from "react-icons/md";

type UploadStatus = "idle" | "uploading" | "success" | "error";

interface UploadResponse {
  message: string;
  filename: string;
  original_filename: string;
  file_url: string;
  file_size: number;
}

export default function FileUploader() {
  const [files, setFiles] = useState<File[]>([]);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(selectedFiles);
    }
  }

  function removeFile(index: number) {
    setFiles(files.filter((_, i) => i !== index));
  }

  async function handleFileUpload() {
    if (!files || files.length === 0) {
      console.log("No files selected, returning");
      return;
    }
    setStatus("uploading");
    setUploadProgress(0);

    const formData = new FormData();
    
    // Append all files to FormData
    files.forEach((file, index) => {
      formData.append(`file_upload_${index}`, file);
    });

    try {
      //Dává se post na backend, kde běž aplikace s endpointem upload
      //It sends the request to the backend
      const response = await axios.post(
        "http://127.0.0.1:2024/uploadfile/",
        formData,
        {
          onUploadProgress: (progressEvent) => {
            const progress = progressEvent.total
              ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
              : 0;
            setUploadProgress(progress);
          },
        }
      );

      const result: UploadResponse = response.data;
      setUploadResult(result);

      setStatus("success");
      setUploadProgress(100);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error("Axios error details:");
        console.error("- Status:", error.response?.status);
        console.error("- Status text:", error.response?.statusText);
        console.error("- Response data:", error.response?.data);
        console.error("- Request URL:", error.config?.url);
        console.error("- Request method:", error.config?.method);
        console.error("- Request headers:", error.config?.headers);

        // Log the specific error message
        if (error.response?.status === 400) {
          console.error("400 Bad Request - Backend rejected the request");
          console.error("Backend response:", error.response?.data);
        }
      } else {
        console.error("Non-axios error:", error);
      }

      setStatus("error");
      setUploadProgress(0);
    }
  }

  return (
    <div className="space-y-4">
      {/* Hidden file input */}
      <input
        type="file"
        onChange={handleFileChange}
        className="hidden"
        id="file-upload"
        multiple
      />

      {/* Upload button styled like the image */}
      <label
        htmlFor="file-upload"
        className="inline-flex items-center gap-2 px-6 py-3 bg-gray-800 text-white rounded-full cursor-pointer hover:bg-gray-700 transition-colors shadow-lg"
      >
        <MdDriveFolderUpload className="text-lg" />
        <span className="font-medium">Upload</span>
      </label>

      {files.length > 0 && (
        <div className="mb-4 space-y-2">
          <h3 className="font-medium text-sm">Selected Files:</h3>
          {files.map((file, index) => (
            <div key={index} className="text-sm border rounded p-2 flex justify-between items-start">
              <div>
                <p>File name: {file.name}</p>
                <p>Size: {(file.size / 1024).toFixed(2)} KB</p>
                <p>Type: {file.type}</p>
              </div>
              <button
                onClick={() => removeFile(index)}
                className="text-red-500 hover:text-red-700 text-lg"
                title="Remove file"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {status === "uploading" && (
        <div className="space-y-2">
          <div className="h-2.5 w-full rounded-full bg-gray-200">
            <div
              className="h-2.5 rounded-full bg-blue-600 transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600">{uploadProgress}% uploaded</p>
        </div>
      )}

      {files.length > 0 && status !== "uploading" && (
        <button
          onClick={handleFileUpload}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Start Upload ({files.length} file{files.length !== 1 ? 's' : ''})
        </button>
      )}

      {status === "success" && (
        <p className="text-sm text-green-600">File uploaded successfully!</p>
      )}

      {status === "error" && (
        <p className="text-sm text-red-600">Upload failed. Please try again.</p>
      )}
    </div>
  );
}
