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

// Helper function to get file type from extension
function getFileType(filename: string): string {
  const extension = filename.toLowerCase().split(".").pop() || "";

  if (["pdf"].includes(extension)) return "PDF";
  if (["docx", "doc"].includes(extension)) return "Word";
  if (["pptx", "ppt"].includes(extension)) return "PowerPoint";
  if (["xlsx", "xls"].includes(extension)) return "Excel";
  if (
    ["txt", "md", "csv", "json", "xml", "html", "htm", "log"].includes(
      extension
    )
  )
    return "Text";

  return "Unknown";
}

// Helper function to get file type color
function getFileTypeColor(fileType: string): string {
  switch (fileType) {
    case "PDF":
      return "bg-red-100 text-red-800";
    case "Word":
      return "bg-blue-100 text-blue-800";
    case "PowerPoint":
      return "bg-orange-100 text-orange-800";
    case "Excel":
      return "bg-green-100 text-green-800";
    case "Text":
      return "bg-gray-100 text-gray-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
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

    // Append all files to FormData with the correct field name for FastAPI
    files.forEach((file) => {
      formData.append("files", file);
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
        accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.txt,.md,.csv,.json,.xml,.html,.htm,.log"
      />

      {/* Upload button styled like the image */}
      <label
        htmlFor="file-upload"
        className="inline-flex items-center gap-2 px-6 py-3 bg-gray-800 text-white rounded-full cursor-pointer hover:bg-gray-700 transition-colors shadow-lg"
      >
        <MdDriveFolderUpload className="text-lg" />
        <span className="font-medium">Upload</span>
      </label>

      {/* Supported file types information */}
      <div className="text-xs text-gray-600 mt-2">
        <p className="font-medium mb-1">Supported file types:</p>
        <div className="flex flex-wrap gap-1">
          <span className="px-2 py-1 bg-gray-100 rounded text-xs">PDF</span>
          <span className="px-2 py-1 bg-gray-100 rounded text-xs">
            Word (.docx, .doc)
          </span>
          <span className="px-2 py-1 bg-gray-100 rounded text-xs">
            PowerPoint (.pptx, .ppt)
          </span>
          <span className="px-2 py-1 bg-gray-100 rounded text-xs">
            Excel (.xlsx, .xls)
          </span>
          <span className="px-2 py-1 bg-gray-100 rounded text-xs">
            Text (.txt, .md, .csv)
          </span>
        </div>
      </div>

      {files.length > 0 && (
        <div className="mb-4 space-y-2">
          <h3 className="font-medium text-sm">Selected Files:</h3>
          {files.map((file, index) => {
            const fileType = getFileType(file.name);
            const colorClass = getFileTypeColor(fileType);

            return (
              <div
                key={index}
                className="text-sm border rounded p-2 flex justify-between items-start"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-medium">{file.name}</p>
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${colorClass}`}
                    >
                      {fileType}
                    </span>
                  </div>
                  <p className="text-gray-600">
                    Size: {(file.size / 1024).toFixed(2)} KB
                  </p>
                  {file.type && (
                    <p className="text-gray-600">MIME: {file.type}</p>
                  )}
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="text-red-500 hover:text-red-700 text-lg ml-2"
                  title="Remove file"
                >
                  ×
                </button>
              </div>
            );
          })}
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
          Start Upload ({files.length} file{files.length !== 1 ? "s" : ""})
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
