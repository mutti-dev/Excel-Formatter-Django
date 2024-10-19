import React, { useState } from 'react';
import { AiOutlineCloudUpload, AiOutlineDownload } from 'react-icons/ai';
import { FaSpinner } from 'react-icons/fa';
import { MdOutlineInsertDriveFile } from 'react-icons/md';

const Formatter = () => {
  const [file, setFile] = useState(null);
  const [practiceId, setPracticeId] = useState('');
  const [fileType, setFileType] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [convertedFile, setConvertedFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setConvertedFile(null);
    setError(''); // Reset error on file select
  };

  const getAcceptedFileTypes = () => {
    switch (fileType) {
      case 'image':
        return 'image/jpeg, image/png'; // Accept only image files (JPG, PNG)
      case 'pdf':
        return 'application/pdf'; // Accept only PDF files
      case 'excel':
        return 'application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'; // Accept Excel files
      default:
        return ''; // No restriction
    }
  };

  const handleConvert = async () => {
    if (!file || !practiceId || !fileType) {
      setError('All fields are required!');
      return;
    }

    setLoading(true);
    setError(''); // Reset error when conversion starts

    const formData = new FormData();
    formData.append('file', file);
    formData.append('practiceId', practiceId);
    formData.append('fileType', fileType);

    try {
      const response = await fetch('http://127.0.0.1:8000/format/', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setConvertedFile(url);
      } else {
        setError('File conversion failed! Please try again.');
      }
    } catch (error) {
      setError('An error occurred while uploading. Please check your connection.');
    }

    setLoading(false);
  };

  return (
    <div style={styles.container}>
      <div style={styles.logoContainer}>
        <MdOutlineInsertDriveFile style={styles.logoIcon} />
      </div>

      <h1 style={styles.title}>OCR File Upload</h1>

      {error && <p style={styles.errorText}>{error}</p>}

      <div style={styles.inputContainer}>
        <input
          type="text"
          id="practiceId"
          value={practiceId}
          onChange={(e) => setPracticeId(e.target.value)}
          style={styles.textInput}
          placeholder="Enter Practice ID"
        />
      </div>

      <div style={styles.inputContainer}>
        <select
          id="fileType"
          value={fileType}
          onChange={(e) => setFileType(e.target.value)}
          style={styles.dropdown}
          disabled={!practiceId}
        >
          <option value="">Select file type</option>
          <option value="image">Image (JPG, PNG)</option>
          <option value="pdf">PDF</option>
          <option value="excel">Excel</option>
        </select>
      </div>

      <div style={styles.fileInputContainer}>
        <label htmlFor="fileInput" style={styles.fileInputLabel}>
          <AiOutlineCloudUpload style={styles.uploadIcon} />
          <span>{file ? file.name : 'Choose a file to upload'}</span>
        </label>
        <input
          type="file"
          id="fileInput"
          onChange={handleFileChange}
          style={styles.fileInput}
          accept={getAcceptedFileTypes()}
          disabled={!practiceId || !fileType}
        />
      </div>

      <button
        onClick={handleConvert}
        disabled={loading || !file || !practiceId || !fileType}
        style={styles.button}
      >
        {loading ? <FaSpinner style={styles.spinnerIcon} /> : 'Convert'}
      </button>

      {loading && <p style={styles.loadingText}>Processing your file...</p>}

      {convertedFile && (
        <a href={convertedFile} download="converted_file" style={styles.downloadLink}>
          <button style={styles.downloadButton}>
            <AiOutlineDownload style={styles.downloadIcon} /> Download Converted File
          </button>
        </a>
      )}
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '40px',
    borderRadius: '15px',
    boxShadow: '0 0 25px rgba(0, 0, 0, 0.1)',
    backgroundColor: '#254B97',
    maxWidth: '600px',
    margin: 'auto',
    transition: 'all 0.3s ease-in-out',
  },
  logoContainer: {
    textAlign: 'center',
    marginBottom: '20px',
  },
  logoIcon: {
    fontSize: '100px',
    color: '#ffffff',
    animation: 'bounce 2s infinite ease-in-out',
  },
  title: {
    fontSize: '32px',
    color: '#ffffff',
    fontWeight: 'bold',
    marginBottom: '25px',
  },

  title1: {
    fontSize: '20px',
    color: '#ffffff',
    fontWeight: 'bold',
    marginBottom: '25px',
  },
  inputContainer: {
    width: '100%',
    marginBottom: '20px',
  },
  label: {
    fontSize: '16px',
    color: '#34495e',
    marginBottom: '8px',
    display: 'block',
  },
  textInput: {
    width: '100%',
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid #bdc3c7',
    fontSize: '16px',
    backgroundColor: '#ecf0f1',
    transition: 'all 0.3s ease',
  },
  dropdown: {
    width: '100%',
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid #bdc3c7',
    fontSize: '16px',
    backgroundColor: '#ecf0f1',
  },
  fileInputContainer: {
    width: '100%',
    marginBottom: '20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  fileInputLabel: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '12px 24px',
    backgroundColor: '#3498db',
    borderRadius: '8px',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '16px',
    transition: 'background-color 0.3s ease',
  },
  uploadIcon: {
    fontSize: '24px',
    color: '#fff',
  },
  fileInput: {
    display: 'none',
  },
  button: {
    padding: '12px 24px',
    backgroundColor: '#2ecc71',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '16px',
    marginTop: '20px',
    transition: 'background-color 0.3s ease',
  },
  downloadButton: {
    padding: '12px 24px',
    backgroundColor: '#e74c3c',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: '20px',
    gap: '10px',
    transition: 'background-color 0.3s ease',
  },
  downloadLink: {
    textDecoration: 'none',
  },
  spinnerIcon: {
    fontSize: '20px',
    color: '#fff',
    animation: 'spin 1s linear infinite',
  },
  loadingText: {
    fontSize: '16px',
    color: '#7f8c8d',
    marginTop: '10px',
  },
};

export default Formatter;
