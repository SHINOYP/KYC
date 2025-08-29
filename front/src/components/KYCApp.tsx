import React, { useState, useCallback, useRef } from 'react';
import { AlertCircle, CheckCircle, Upload, File, X } from 'lucide-react';

// Simple File Upload Component
const FileUpload = ({ onFilesSelect, isLoading }) => {
  const [idCardFile, setIdCardFile] = useState(null);
  const [selfieFile, setSelfieFile] = useState(null);
  const idInputRef = useRef(null);
  const selfieInputRef = useRef(null);

  const handleFileSelect = (file, type) => {
    // Validate file
    const validationError = validateFile(file);
    if (validationError) {
      alert(validationError);
      return;
    }

    if (type === 'id') {
      if (idCardFile?.preview) URL.revokeObjectURL(idCardFile.preview);
      const newFile = { file, preview: URL.createObjectURL(file) };
      setIdCardFile(newFile);
      onFilesSelect({ idCard: file, selfie: selfieFile?.file || null });
    } else {
      if (selfieFile?.preview) URL.revokeObjectURL(selfieFile.preview);
      const newFile = { file, preview: URL.createObjectURL(file) };
      setSelfieFile(newFile);
      onFilesSelect({ idCard: idCardFile?.file || null, selfie: file });
    }
  };

  const validateFile = (file) => {
    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      return 'File size must be less than 10MB';
    }

    // Check file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      return 'Please upload a valid image file (JPEG, PNG, WebP)';
    }

    return null;
  };

  const handleFileRemove = (type) => {
    if (type === 'id') {
      if (idCardFile?.preview) URL.revokeObjectURL(idCardFile.preview);
      setIdCardFile(null);
      onFilesSelect({ idCard: null, selfie: selfieFile?.file || null });
    } else {
      if (selfieFile?.preview) URL.revokeObjectURL(selfieFile.preview);
      setSelfieFile(null);
      onFilesSelect({ idCard: idCardFile?.file || null, selfie: null });
    }
  };

  const UploadArea = ({ type, title, description, uploadedFile, inputRef }) => (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center min-h-[200px] flex flex-col justify-center hover:border-blue-400 transition-colors">
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFileSelect(file, type);
        }}
        className="hidden"
        disabled={isLoading}
      />

      {uploadedFile ? (
        <div className="space-y-3">
          <div className="relative inline-block">
            <img
              src={uploadedFile.preview}
              alt={`${type} preview`}
              className="w-32 h-24 object-cover rounded-lg mx-auto shadow-lg"
            />
            <button
              onClick={() => handleFileRemove(type)}
              className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600"
              disabled={isLoading}
            >
              <X className="w-3 h-3" />
            </button>
          </div>
          <div className="flex items-center justify-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-sm font-medium text-green-600">File uploaded</span>
          </div>
          <p className="text-xs text-gray-600 truncate">{uploadedFile.file.name}</p>
          <button
            onClick={() => inputRef.current?.click()}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-md text-sm"
            disabled={isLoading}
          >
            Change File
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <File className="w-12 h-12 mx-auto text-gray-400" />
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="text-sm text-gray-600">{description}</p>
          <button
            onClick={() => inputRef.current?.click()}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-md font-medium transition-colors"
            disabled={isLoading}
          >
            Select File
          </button>
          <p className="text-xs text-gray-500">JPEG, PNG, WebP • Max 10MB</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Upload Your Documents</h2>
        <p className="text-gray-600">
          Please upload your ID document and a clear selfie for verification
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <UploadArea
          type="id"
          title="ID Document"
          description="Upload a clear photo of your government-issued ID"
          uploadedFile={idCardFile}
          inputRef={idInputRef}
        />

        <UploadArea
          type="selfie"
          title="Selfie Photo"
          description="Take a clear selfie matching your ID document"
          uploadedFile={selfieFile}
          inputRef={selfieInputRef}
        />
      </div>
    </div>
  );
};

// Progress Bar Component
const ProgressBar = ({ currentStep, isLoading }) => {
  const steps = [
    { number: 1, title: 'Upload Documents', description: 'Select your files' },
    { number: 2, title: 'Uploading', description: 'Sending files securely' },
    { number: 3, title: 'Analyzing', description: 'AI processing documents' },
    { number: 4, title: 'Complete', description: 'Verification finished' }
  ];

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4">
        {steps.map((step, index) => (
          <div key={step.number} className="flex items-center">
            <div className={`
              flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all
              ${currentStep >= step.number
                ? 'bg-blue-500 border-blue-500 text-white'
                : 'border-gray-300 text-gray-400'
              }
              ${currentStep === step.number && isLoading ? 'animate-pulse' : ''}
            `}>
              {step.number}
            </div>
            {index < steps.length - 1 && (
              <div className={`
                w-16 h-1 mx-2 transition-colors
                ${currentStep > step.number ? 'bg-blue-500' : 'bg-gray-300'}
              `} />
            )}
          </div>
        ))}
      </div>
      <div className="text-center">
        <h3 className="font-semibold">{steps[currentStep - 1]?.title}</h3>
        <p className="text-sm text-gray-600">{steps[currentStep - 1]?.description}</p>
      </div>
    </div>
  );
};

// Result Card Component
const ResultCard = ({ result }) => (
  <div className="bg-white border rounded-lg p-6 space-y-4">
    <div className="text-center">
      {result.status === 'rejected' ? (
        <>
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-red-600 mb-2">Verification Failed!</h2>
        </>
      ) : (
        <>
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-green-600 mb-2">Verification {result.status}!</h2>
        </>
      )}
    </div>

    <div className="grid md:grid-cols-2 gap-4">
      <div className="space-y-2">

        <h3 className="font-semibold">Extracted Information:</h3>
        <div className="bg-gray-50 p-3 rounded text-sm space-y-1">
          <p><strong>Name:</strong> {result.extracted.name}</p>
          <p><strong>Date of Birth:</strong> {result.extracted.dob}</p>
          <p><strong>ID Number:</strong> {result.extracted.id_number}</p>
          <p><strong>Document Type:</strong> {result.extracted.document_type}</p>
          <p><strong>Verification Status:</strong> {result.status}</p>
          {result.fraud_flags.flags.length > 0 && (
            <div className="mt-2">
              <h4 className="font-semibold">Fraud Flags:</h4>
              <ul className="list-disc list-inside">
                {result.fraud_flags.flags.map((flag, index) => (
                  <li key={index} className="text-sm text-red-600">{flag}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="font-semibold">Trust Score:</h3>
        <div className="flex items-center space-x-2">
          <div className="flex-1 bg-gray-200 rounded-full h-3">
            <div
              className="bg-green-500 h-3 rounded-full transition-all duration-500"
              style={{ width: `${result.trust_score}%` }}
            />
          </div>
          <span className="font-bold text-green-600">{result.trust_score}%</span>
        </div>
      </div>
    </div>

    <div>
      <h3 className="font-semibold mb-2">Summary:</h3>
      <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded leading-relaxed">
        {result.summary}
      </p>
    </div>
  </div>
);

// Main KYC App Component
const KYCApp = () => {
  const [files, setFiles] = useState({ idCard: null, selfie: null });
  const [verification, setVerification] = useState({
    step: 1,
    isLoading: false,
    result: null,
    error: null
  });
  const [apiHealth, setApiHealth] = useState({ status: 'unknown', lastChecked: null });
  console.log("API Health:", verification);
  // Check API health on component mount
  React.useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/kyc/health', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const healthData = await response.json();
        setApiHealth({
          status: 'healthy',
          lastChecked: new Date().toLocaleTimeString(),
          data: healthData
        });
      } else {
        setApiHealth({
          status: 'error',
          lastChecked: new Date().toLocaleTimeString(),
          error: `HTTP ${response.status}`
        });
      }
    } catch (error) {
      console.error('Health check failed:', error);
      setApiHealth({
        status: 'error',
        lastChecked: new Date().toLocaleTimeString(),
        error: error.message
      });
    }
  };

  const handleFilesSelect = (newFiles) => {
    console.log('Files selected:', newFiles);
    setFiles(newFiles);
    if (verification.result) {
      setVerification({
        step: 1,
        isLoading: false,
        result: null,
        error: null
      });
    }
  };

  const handleVerifyKYC = async () => {
    if (!files.idCard || !files.selfie) {
      alert('Please upload both ID document and selfie before verification.');
      return;
    }

    setVerification({
      step: 2,
      isLoading: true,
      result: null,
      error: null
    });

    try {
      // Uploading step
      setVerification(prev => ({ ...prev, step: 3 }));

      const formData = new FormData();
      formData.append('id_card', files.idCard);
      formData.append('selfie', files.selfie);

      console.log('Sending verification request...');

      const response = await fetch('http://127.0.0.1:8000/api/v1/kyc/verify', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const apiResult = await response.json();
      console.log('API Response:', apiResult);

      // Transform API response to match UI structure
      const transformedResult = {
        verification_id: apiResult.verification_id,
        success: apiResult.success,
        extracted: {
          name: apiResult.name || 'Unknown',
          dob: apiResult.dob || 'Unknown',
          id_number: apiResult.id_number || 'Unknown',
          document_type: apiResult.document_type || 'unknown'
        },
        trust_score: apiResult.trust_score ?? 0,
        face_confidence: apiResult.face_confidence ?? 0,
        fraud_flags: {
          has_fraud_indicators: apiResult.fraud_flags?.has_fraud_indicators ?? false,
          risk_level: apiResult.fraud_flags?.risk_level || 'unknown',
          flags: apiResult.fraud_flags?.flags || [],
          summary: apiResult.fraud_flags?.summary || '',
          details: {
            age_validation: apiResult.fraud_flags?.details?.age_validation || {},
            expiry_validation: apiResult.fraud_flags?.details?.expiry_validation || {},
            name_validation: apiResult.fraud_flags?.details?.name_validation || {},
            id_validation: apiResult.fraud_flags?.details?.id_validation || {},
            consistency_issues: apiResult.fraud_flags?.details?.consistency_issues || []
          }
        },
        summary: apiResult.summary || 'Verification completed.',
        status: apiResult.status || 'completed',
        timestamp: apiResult.timestamp,
        processing_time: apiResult.processing_time_ms
      };

      setVerification({
        step: 4,
        isLoading: false,
        result: transformedResult,
        error: null
      });

    } catch (error) {
      console.error('Verification error:', error);
      setVerification({
        step: 1,
        isLoading: false,
        result: null,
        error: `Verification failed: ${error.message}`
      });
    }
  };

  const handleStartOver = () => {
    setFiles({ idCard: null, selfie: null });
    setVerification({
      step: 1,
      isLoading: false,
      result: null,
      error: null
    });
  };

  const canProceed = files.idCard && files.selfie && !verification.isLoading;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            AI-Powered KYC Verification
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Secure, fast, and reliable identity verification using advanced AI technology
          </p>

          {/* API Health */}
          <div className="mt-4 flex items-center justify-center space-x-2">
            <div
              className={`w-3 h-3 rounded-full ${apiHealth.status === 'healthy'
                ? 'bg-green-500'
                : apiHealth.status === 'error'
                  ? 'bg-red-500'
                  : 'bg-yellow-500'
                }`}
            />
            <span className="text-sm text-gray-600">
              API Status: {apiHealth.status === 'healthy' ? 'Online' :
                apiHealth.status === 'error' ? 'Offline' : 'Checking...'}
              {apiHealth.lastChecked && ` (${apiHealth.lastChecked})`}
            </span>
            <button
              onClick={checkApiHealth}
              className="text-xs text-blue-500 hover:text-blue-700 ml-2"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <ProgressBar currentStep={verification.step} isLoading={verification.isLoading} />
        </div>

        {/* Error Alert */}
        {verification.error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-700">{verification.error}</span>
          </div>
        )}

        {/* Main Content */}
        {verification.result ? (
          <div className="space-y-6">
            <ResultCard result={verification.result} />
            <div className="text-center">
              <button
                onClick={handleStartOver}
                className="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg font-medium transition-colors"
              >
                Verify Another Identity
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <FileUpload onFilesSelect={handleFilesSelect} isLoading={verification.isLoading} />
            </div>

            {(files.idCard || files.selfie) && (
              <div className="text-center">
                <button
                  onClick={handleVerifyKYC}
                  disabled={!canProceed}
                  className={`
                    px-8 py-4 rounded-lg font-semibold text-white min-w-[200px] transition-all
                    ${canProceed
                      ? 'bg-blue-500 hover:bg-blue-600 hover:shadow-lg'
                      : 'bg-gray-400 cursor-not-allowed'
                    }
                  `}
                >
                  {verification.isLoading ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Verifying...</span>
                    </div>
                  ) : (
                    <>
                      <CheckCircle className="w-5 h-5 inline mr-2" />
                      Start Verification
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Debug Info */}
        <div className="mt-8 bg-gray-100 rounded-lg p-4 text-sm text-gray-600">
          <p><strong>Debug Info:</strong></p>
          <p>ID Card: {files.idCard ? `✓ ${files.idCard.name} (${(files.idCard.size / 1024 / 1024).toFixed(2)}MB)` : '✗ Not uploaded'}</p>
          <p>Selfie: {files.selfie ? `✓ ${files.selfie.name} (${(files.selfie.size / 1024 / 1024).toFixed(2)}MB)` : '✗ Not uploaded'}</p>
          <p>Step: {verification.step} | Loading: {verification.isLoading ? 'Yes' : 'No'}</p>
          <p>API Health: {apiHealth.status} {apiHealth.error && `(${apiHealth.error})`}</p>
          <p>Base URL: http://127.0.0.1:8000</p>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-gray-500">
          <p>🔒 Your documents are processed securely and are not stored on our servers</p>
        </div>
      </div>
    </div>
  );
};

export default KYCApp;