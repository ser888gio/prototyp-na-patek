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
  const [file_upload, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  }

  async function handleFileUpload() {
    if (!file_upload) {
      console.log("No file selected, returning");
      return;
    }
    setStatus("uploading");
    setUploadProgress(0);

    const formData = new FormData();
    formData.append("file_upload", file_upload);

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
      />

      {/* Upload button styled like the image */}
      <label
        htmlFor="file-upload"
        className="inline-flex items-center gap-2 px-6 py-3 bg-gray-800 text-white rounded-full cursor-pointer hover:bg-gray-700 transition-colors shadow-lg"
      >
        <MdDriveFolderUpload className="text-lg" />
        <span className="font-medium">Upload</span>
      </label>

      {file_upload && (
        <div className="mb-4 text-sm">
          <p>File name: {file_upload.name}</p>
          <p>Size: {(file_upload.size / 1024).toFixed(2)} KB</p>
          <p>Type: {file_upload.type}</p>
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

      {file_upload && status !== "uploading" && (
        <button
          onClick={handleFileUpload}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Start Upload
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
