import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface FileUploadProps {
  onFilesSelect: (files: { idCard: File | null; selfie: File | null }) => void;
  isLoading?: boolean;
}

interface UploadedFile {
  file: File;
  preview: string;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFilesSelect, isLoading = false }) => {
  const [idCardFile, setIdCardFile] = useState<UploadedFile | null>(null);
  const [selfieFile, setSelfieFile] = useState<UploadedFile | null>(null);

  const createFileWithPreview = (file: File): UploadedFile => ({
    file,
    preview: URL.createObjectURL(file)
  });

  const onDropIdCard = useCallback((acceptedFiles: File[]) => {
    console.log('ID Card files dropped:', acceptedFiles); // Debug log
    if (acceptedFiles.length > 0) {
      if (idCardFile) URL.revokeObjectURL(idCardFile.preview);

      const newFile = createFileWithPreview(acceptedFiles[0]);
      setIdCardFile(newFile);
      onFilesSelect({
        idCard: acceptedFiles[0],
        selfie: selfieFile?.file || null
      });
    }
  }, [selfieFile, idCardFile, onFilesSelect]);

  const onDropSelfie = useCallback((acceptedFiles: File[]) => {
    console.log('Selfie files dropped:', acceptedFiles); // Debug log
    if (acceptedFiles.length > 0) {
      if (selfieFile) URL.revokeObjectURL(selfieFile.preview);

      const newFile = createFileWithPreview(acceptedFiles[0]);
      setSelfieFile(newFile);
      onFilesSelect({
        idCard: idCardFile?.file || null,
        selfie: acceptedFiles[0]
      });
    }
  }, [idCardFile, selfieFile, onFilesSelect]);

  // ID Card Dropzone
  const idDropzone = useDropzone({
    onDrop: onDropIdCard,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp']
    },
    maxFiles: 1,
    disabled: isLoading
  });

  // Selfie Dropzone
  const selfieDropzone = useDropzone({
    onDrop: onDropSelfie,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp']
    },
    maxFiles: 1,
    disabled: isLoading
  });

  const removeFile = (type: 'id' | 'selfie') => {
    if (type === 'id') {
      if (idCardFile) URL.revokeObjectURL(idCardFile.preview);
      setIdCardFile(null);
      onFilesSelect({ idCard: null, selfie: selfieFile?.file || null });
    } else {
      if (selfieFile) URL.revokeObjectURL(selfieFile.preview);
      setSelfieFile(null);
      onFilesSelect({ idCard: idCardFile?.file || null, selfie: null });
    }
  };

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (idCardFile) URL.revokeObjectURL(idCardFile.preview);
      if (selfieFile) URL.revokeObjectURL(selfieFile.preview);
    };
  }, []);

  const UploadArea = ({
    type,
    title,
    description,
    dropzone,
    uploadedFile
  }: {
    type: 'id' | 'selfie';
    title: string;
    description: string;
    dropzone: any;
    uploadedFile: UploadedFile | null;
  }) => {
    const { getRootProps, getInputProps, isDragActive, open } = dropzone;

    return (
      <Card className="relative overflow-hidden">
        <div
          {...getRootProps()}
          className={`
            p-8 border-2 border-dashed rounded-lg min-h-[200px]
            transition-colors duration-200
            ${isDragActive ? 'border-blue-500 bg-blue-50 dark:bg-blue-950' : 'border-gray-300 dark:border-gray-600'}
            ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-blue-400'}
            ${uploadedFile ? 'border-green-500 bg-green-50 dark:bg-green-950' : ''}
          `}
          onClick={!isLoading ? open : undefined}
        >
          <input {...getInputProps()} />

          {uploadedFile ? (
            <div className="text-center">
              <div className="relative inline-block mb-4">
                <img
                  src={uploadedFile.preview}
                  alt={`${type} preview`}
                  className="w-32 h-24 object-cover rounded-lg mx-auto shadow-lg"
                />
                <Button
                  size="sm"
                  variant="destructive"
                  className="absolute -top-2 -right-2 w-6 h-6 rounded-full p-0 shadow-md"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(type);
                  }}
                  disabled={isLoading}
                >
                  <X className="w-3 h-3" />
                </Button>
              </div>
              <div className="flex items-center justify-center space-x-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-sm font-medium text-green-600">
                  File uploaded successfully
                </span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 truncate max-w-full mb-3">
                {uploadedFile.file.name}
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  open();
                }}
                disabled={isLoading}
              >
                Change File
              </Button>
            </div>
          ) : (
            <div className="text-center h-full flex flex-col justify-center">
              <div className="mb-4">
                {isDragActive ? (
                  <Upload className="w-12 h-12 mx-auto text-blue-500" />
                ) : (
                  <File className="w-12 h-12 mx-auto text-gray-400" />
                )}
              </div>

              <h3 className="text-lg font-semibold mb-2">{title}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{description}</p>

              <div className="text-xs text-gray-500 dark:text-gray-400">
                {isDragActive ? (
                  <span className="text-blue-500 font-medium">Drop your file here</span>
                ) : (
                  <div>
                    <span>Drop your file here or </span>
                    <button
                      type="button"
                      className="text-blue-500 font-medium hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded px-1"
                      onClick={(e) => {
                        e.stopPropagation();
                        open();
                        console.log('Browse button clicked'); // Debug log
                      }}
                      disabled={isLoading}
                    >
                      click to browse
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Upload Your Documents</h2>
        <p className="text-gray-600 dark:text-gray-400">
          Please upload your ID document and a clear selfie for verification
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <UploadArea
          type="id"
          title="ID Document"
          description="Upload a clear photo of your government-issued ID"
          dropzone={idDropzone}
          uploadedFile={idCardFile}
        />

        <UploadArea
          type="selfie"
          title="Selfie Photo"
          description="Take a clear selfie matching your ID document"
          dropzone={selfieDropzone}
          uploadedFile={selfieFile}
        />
      </div>

      <div className="text-center text-sm text-gray-500 dark:text-gray-400 space-y-1">
        <p>Supported formats: JPEG, PNG, WebP</p>
        <p>Maximum file size: 10MB per file</p>
      </div>

      {/* Debug Info (remove in production) */}
      <div className="text-xs text-gray-400 mt-4 p-2 bg-gray-100 dark:bg-gray-800 rounded">
        <p>Debug: ID Card - {idCardFile ? 'Uploaded' : 'Not uploaded'}</p>
        <p>Debug: Selfie - {selfieFile ? 'Uploaded' : 'Not uploaded'}</p>
        <p>Debug: Loading - {isLoading ? 'Yes' : 'No'}</p>
      </div>
    </div>
  );
};

export default FileUpload;