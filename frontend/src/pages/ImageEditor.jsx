import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import client from '../api/client';
import './ImageEditor.css';

const OPERATIONS = [
  { key: 'histogram_equalization', label: 'Histogram Equalization', icon: '📊', desc: 'Improve contrast' },
  { key: 'noise_reduction', label: 'Noise Reduction', icon: '🔇', desc: 'Remove noise' },
  { key: 'blur', label: 'Gaussian Blur', icon: '💧', desc: 'Smooth / soften' },
  { key: 'sharpen', label: 'Sharpen', icon: '🔪', desc: 'Increase detail' },
  { key: 'edge_detection', label: 'Edge Detection', icon: '📐', desc: 'Canny edges' },
  { key: 'grayscale', label: 'Grayscale', icon: '🌑', desc: 'Black & white' },
  { key: 'sepia', label: 'Sepia', icon: '🎞️', desc: 'Vintage tone' },
  { key: 'invert', label: 'Invert', icon: '🔄', desc: 'Invert colors' },
];

const FORMATS = ['png', 'jpg', 'webp', 'bmp', 'tiff'];

export default function ImageEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [convertFormat, setConvertFormat] = useState('png');

  useEffect(() => {
    client.get(`/images/${id}`).then(({ data }) => {
      setImage(data.image);
      setLoading(false);
    }).catch(() => {
      navigate('/dashboard');
    });
  }, [id]);

  const handleProcess = async (operation) => {
    setProcessing(true);
    setResult(null);
    try {
      const { data } = await client.post(`/images/${id}/process`, { operation });
      setResult(data.image);
    } catch (err) {
      alert(err.response?.data?.errors?.[0] || 'Processing failed.');
    } finally {
      setProcessing(false);
    }
  };

  const handleConvert = async () => {
    setProcessing(true);
    setResult(null);
    try {
      const { data } = await client.post(`/images/${id}/convert`, { format: convertFormat });
      setResult(data.image);
    } catch (err) {
      alert(err.response?.data?.errors?.[0] || 'Conversion failed.');
    } finally {
      setProcessing(false);
    }
  };

  const handleDownload = (imgData) => {
    const link = document.createElement('a');
    link.href = `${client.defaults.baseURL}/images/files/${imgData.filename}`;
    link.download = imgData.original_filename;
    link.click();
  };

  if (loading) {
    return <div className="editor-loading"><span className="spinner"></span></div>;
  }

  const imgSrc = (imgData) =>
    `${client.defaults.baseURL}/images/files/${imgData.filename}`;

  return (
    <div className="editor animate-fade-in">
      {/* Preview area */}
      <div className="editor-preview">
        <div className="preview-panel">
          <h3>Original</h3>
          <div className="preview-image">
            <img src={imgSrc(image)} alt="Original" />
          </div>
          <div className="preview-meta">
            <span>{image.original_filename}</span>
            <span>{image.width}×{image.height}</span>
          </div>
        </div>

        <div className="preview-arrow">→</div>

        <div className="preview-panel">
          <h3>Result</h3>
          <div className="preview-image">
            {processing ? (
              <div className="preview-loading">
                <span className="spinner"></span>
                <p>Processing…</p>
              </div>
            ) : result ? (
              <img src={imgSrc(result)} alt="Result" />
            ) : (
              <div className="preview-placeholder">
                <p>Select an operation</p>
              </div>
            )}
          </div>
          {result && (
            <div className="preview-meta">
              <span>{result.original_filename}</span>
              <span>{result.width}×{result.height}</span>
              <button className="btn btn-primary btn-sm" onClick={() => handleDownload(result)}>
                ↓ Download
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="editor-controls">
        <div className="control-section card">
          <h3>🎨 Image Processing</h3>
          <div className="ops-grid">
            {OPERATIONS.map((op) => (
              <button
                key={op.key}
                className="op-btn"
                onClick={() => handleProcess(op.key)}
                disabled={processing}
              >
                <span className="op-icon">{op.icon}</span>
                <span className="op-label">{op.label}</span>
                <span className="op-desc">{op.desc}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="control-section card">
          <h3>🔄 Format Conversion</h3>
          <div className="convert-row">
            <select
              value={convertFormat}
              onChange={(e) => setConvertFormat(e.target.value)}
              className="convert-select"
            >
              {FORMATS.map((f) => (
                <option key={f} value={f}>{f.toUpperCase()}</option>
              ))}
            </select>
            <button
              className="btn btn-primary"
              onClick={handleConvert}
              disabled={processing}
            >
              Convert
            </button>
          </div>
        </div>

        <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
          ← Back to Dashboard
        </button>
      </div>
    </div>
  );
}
