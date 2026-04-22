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

const PIPELINE_OPERATIONS = [
  { key: 'grayscale', label: 'Grayscale', icon: '🌑', defaultParams: null },
  { key: 'blur', label: 'Gaussian Blur', icon: '💧', defaultParams: { radius: 2 } },
  { key: 'sharpen', label: 'Sharpen', icon: '🔪', defaultParams: null },
  { key: 'edge_detection', label: 'Edge Detection', icon: '📐', defaultParams: null },
  { key: 'resize', label: 'Resize', icon: '📏', defaultParams: { width: 800, height: 800 } },
  { key: 'rotate', label: 'Rotate', icon: '🔃', defaultParams: { angle: 90 } },
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

  // Transform params
  const [resizeWidth, setResizeWidth] = useState('');
  const [resizeHeight, setResizeHeight] = useState('');
  const [cropX, setCropX] = useState('0');
  const [cropY, setCropY] = useState('0');
  const [cropW, setCropW] = useState('');
  const [cropH, setCropH] = useState('');
  const [rotateAngle, setRotateAngle] = useState('90');
  const [compressQuality, setCompressQuality] = useState(75);

  // Pipeline State
  const [pipelineSteps, setPipelineSteps] = useState([]);
  
  // Metadata State
  const [metadata, setMetadata] = useState(null);
  const [showRawJson, setShowRawJson] = useState(false);
  const [showMetadataModal, setShowMetadataModal] = useState(false);

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

  const handleProcessWithParams = async (operation, params) => {
    setProcessing(true);
    setResult(null);
    try {
      const { data } = await client.post(`/images/${id}/process`, { operation, params });
      setResult(data.image);
    } catch (err) {
      alert(err.response?.data?.errors?.[0] || 'Processing failed.');
    } finally {
      setProcessing(false);
    }
  };

  const handleResize = () => {
    const params = {};
    if (resizeWidth) params.width = parseInt(resizeWidth);
    if (resizeHeight) params.height = parseInt(resizeHeight);
    if (!params.width && !params.height) {
      alert('Please enter at least one dimension.');
      return;
    }
    handleProcessWithParams('resize', params);
  };

  const handleCrop = () => {
    const params = {
      x: parseInt(cropX) || 0,
      y: parseInt(cropY) || 0,
    };
    if (cropW) params.width = parseInt(cropW);
    if (cropH) params.height = parseInt(cropH);
    handleProcessWithParams('crop', params);
  };

  const handleRotate = () => {
    const angle = parseFloat(rotateAngle) || 90;
    handleProcessWithParams('rotate', { angle });
  };

  const handleCompress = async () => {
    setProcessing(true);
    setResult(null);
    try {
      const { data } = await client.post(`/images/${id}/compress`, { quality: compressQuality });
      setResult(data.image);
    } catch (err) {
      alert(err.response?.data?.errors?.[0] || 'Compression failed.');
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

  const handleAnalyzeMetadata = async () => {
    try {
      const { data } = await client.get(`/images/${id}/metadata`);
      setMetadata(data.metadata || {});
      setShowMetadataModal(true);
    } catch (err) {
      alert('Failed to read metadata.');
    }
  };

  const handleRemoveMetadata = async () => {
    setProcessing(true);
    setResult(null);
    try {
      const { data } = await client.post(`/images/${id}/remove_metadata`);
      setResult(data.image);
    } catch (err) {
      alert(err.response?.data?.errors?.[0] || 'Failed to remove metadata.');
    } finally {
      setProcessing(false);
    }
  };

  // Pipeline Handlers
  const addPipelineStep = (opKey) => {
    if (!opKey) return;
    const opDef = PIPELINE_OPERATIONS.find((o) => o.key === opKey);
    if (!opDef) return;
    setPipelineSteps([...pipelineSteps, { ...opDef, id: Date.now() + Math.random(), params: opDef.defaultParams ? { ...opDef.defaultParams } : {} }]);
  };

  const updateStepParam = (index, paramKey, val) => {
    const newSteps = [...pipelineSteps];
    newSteps[index].params[paramKey] = val;
    setPipelineSteps(newSteps);
  };

  const moveStep = (index, dir) => {
    if (index + dir < 0 || index + dir >= pipelineSteps.length) return;
    const newSteps = [...pipelineSteps];
    const temp = newSteps[index];
    newSteps[index] = newSteps[index + dir];
    newSteps[index + dir] = temp;
    setPipelineSteps(newSteps);
  };

  const removeStep = (index) => {
    setPipelineSteps(pipelineSteps.filter((_, i) => i !== index));
  };

  const handleRunPipeline = async () => {
    setProcessing(true);
    setResult(null);
    try {
      const payload = pipelineSteps.map(step => {
        const cleanedParams = {};
        for(const [k, v] of Object.entries(step.params)) {
          // Coerce to number if numeric, useful for rotate mostly
          const num = parseFloat(v);
          cleanedParams[k] = isNaN(num) ? v : num;
        }
        return { operation: step.key, params: cleanedParams };
      });
      const { data } = await client.post(`/images/${id}/pipeline`, { pipeline: payload });
      setResult(data.image);
    } catch (err) {
      alert(err.response?.data?.errors?.[0] || 'Pipeline failed.');
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

  const formatBytes = (bytes) => {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(2)} MB`;
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
              <span className="meta-filesize">{formatBytes(result.file_size)}</span>
              <button className="btn btn-primary btn-sm" onClick={() => handleDownload(result)}>
                ↓ Download
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="editor-controls">
        
        {/* Pipeline Builder */}
        <div className="control-section card">
          <h3>🔄 Pipeline Builder</h3>
          <p className="transform-desc" style={{marginBottom: '15px'}}>Chain multiple operations sequentially.</p>
          
          <div className="pipeline-list">
            {pipelineSteps.map((step, idx) => (
              <div key={step.id} className="pipeline-step">
                <div className="step-header">
                  <div className="step-title">
                    <span className="step-number">{idx + 1}</span>
                    <span className="step-icon">{step.icon}</span>
                    <span>{step.label}</span>
                  </div>
                  <div className="step-actions">
                    <button className="step-action-btn" onClick={() => moveStep(idx, -1)} disabled={idx === 0}>⬆</button>
                    <button className="step-action-btn" onClick={() => moveStep(idx, 1)} disabled={idx === pipelineSteps.length - 1}>⬇</button>
                    <button className="step-action-btn danger" onClick={() => removeStep(idx)}>❌</button>
                  </div>
                </div>
                {Object.keys(step.params).length > 0 && (
                  <div className="step-params">
                    {Object.keys(step.params).map(paramKey => (
                      <div key={paramKey} className="input-group-mini" style={{ flex: 'none', width: '80px' }}>
                        <label>{paramKey}</label>
                        <input
                          type="number"
                          value={step.params[paramKey]}
                          onChange={(e) => updateStepParam(idx, paramKey, e.target.value)}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            
            {pipelineSteps.length === 0 && (
              <div className="pipeline-empty">No steps added yet. Choose an operation below.</div>
            )}
          </div>

          <div className="pipeline-add-row mt-2">
            <select
              className="convert-select"
              onChange={(e) => { addPipelineStep(e.target.value); e.target.value = ""; }}
              defaultValue=""
            >
              <option value="" disabled>+ Add Step</option>
              {PIPELINE_OPERATIONS.map(op => (
                <option key={op.key} value={op.key}>{op.label}</option>
              ))}
            </select>
            
            <button 
              className="btn btn-primary" 
              onClick={handleRunPipeline}
              disabled={processing || pipelineSteps.length === 0}
            >
              ▶ Run Pipeline
            </button>
          </div>
        </div>

        {/* Existing Transform Tools ... */}
        {/* Transform Tools */}
        <div className="control-section card">
          <h3>✂️ Transform Tools</h3>
          <div className="transform-grid">
            {/* Resize */}
            <div className="transform-card">
              <div className="transform-header">
                <span className="transform-icon">📐</span>
                <span className="transform-title">Resize</span>
              </div>
              <p className="transform-desc">Scale image to new dimensions</p>
              <div className="transform-inputs">
                <div className="input-pair">
                  <div className="input-group-mini">
                    <label>Width</label>
                    <input
                      type="number"
                      placeholder={image.width}
                      value={resizeWidth}
                      onChange={(e) => setResizeWidth(e.target.value)}
                      min="1"
                    />
                  </div>
                  <span className="input-separator">×</span>
                  <div className="input-group-mini">
                    <label>Height</label>
                    <input
                      type="number"
                      placeholder={image.height}
                      value={resizeHeight}
                      onChange={(e) => setResizeHeight(e.target.value)}
                      min="1"
                    />
                  </div>
                </div>
                <p className="input-hint">Leave one empty to keep aspect ratio</p>
              </div>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleResize}
                disabled={processing}
              >
                Apply Resize
              </button>
            </div>

            {/* Crop */}
            <div className="transform-card">
              <div className="transform-header">
                <span className="transform-icon">✂️</span>
                <span className="transform-title">Crop</span>
              </div>
              <p className="transform-desc">Cut out a region of the image</p>
              <div className="transform-inputs">
                <div className="input-pair">
                  <div className="input-group-mini">
                    <label>X</label>
                    <input
                      type="number"
                      value={cropX}
                      onChange={(e) => setCropX(e.target.value)}
                      min="0"
                    />
                  </div>
                  <div className="input-group-mini">
                    <label>Y</label>
                    <input
                      type="number"
                      value={cropY}
                      onChange={(e) => setCropY(e.target.value)}
                      min="0"
                    />
                  </div>
                </div>
                <div className="input-pair">
                  <div className="input-group-mini">
                    <label>Width</label>
                    <input
                      type="number"
                      placeholder="Full"
                      value={cropW}
                      onChange={(e) => setCropW(e.target.value)}
                      min="1"
                    />
                  </div>
                  <span className="input-separator">×</span>
                  <div className="input-group-mini">
                    <label>Height</label>
                    <input
                      type="number"
                      placeholder="Full"
                      value={cropH}
                      onChange={(e) => setCropH(e.target.value)}
                      min="1"
                    />
                  </div>
                </div>
              </div>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleCrop}
                disabled={processing}
              >
                Apply Crop
              </button>
            </div>

            {/* Rotate */}
            <div className="transform-card">
              <div className="transform-header">
                <span className="transform-icon">🔃</span>
                <span className="transform-title">Rotate</span>
              </div>
              <p className="transform-desc">Rotate image by angle</p>
              <div className="transform-inputs">
                <div className="rotate-presets">
                  {[90, 180, 270].map((a) => (
                    <button
                      key={a}
                      className={`preset-btn ${rotateAngle === String(a) ? 'active' : ''}`}
                      onClick={() => setRotateAngle(String(a))}
                    >
                      {a}°
                    </button>
                  ))}
                </div>
                <div className="input-group-mini">
                  <label>Custom angle (°)</label>
                  <input
                    type="number"
                    value={rotateAngle}
                    onChange={(e) => setRotateAngle(e.target.value)}
                    min="-360"
                    max="360"
                  />
                </div>
              </div>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleRotate}
                disabled={processing}
              >
                Apply Rotate
              </button>
            </div>
          </div>
        </div>

        {/* Image Processing */}
        <div className="control-section card">
          <h3>🎨 Single Operations</h3>
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


        {/* Compress */}
        <div className="control-section card">
          <h3>📦 Compress</h3>
          <div className="compress-row">
            <div className="compress-slider-group">
              <div className="compress-slider-header">
                <label>JPEG Quality</label>
                <span className="quality-value">{compressQuality}%</span>
              </div>
              <input
                type="range"
                min="1"
                max="100"
                value={compressQuality}
                onChange={(e) => setCompressQuality(parseInt(e.target.value))}
                className="quality-slider"
              />
              <div className="slider-labels">
                <span>Small file</span>
                <span>High quality</span>
              </div>
            </div>
            <button
              className="btn btn-primary"
              onClick={handleCompress}
              disabled={processing}
            >
              Compress
            </button>
          </div>
        </div>

        {/* Format Conversion */}
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

        {/* Metadata Tools */}
        <div className="control-section card">
          <h3>🕵️ Metadata Tools</h3>
          <div className="metadata-row" style={{ display: 'flex', gap: '12px' }}>
            <button className="btn btn-secondary" onClick={handleAnalyzeMetadata}>
               View Metadata
            </button>
            <button className="btn btn-danger" onClick={handleRemoveMetadata} disabled={processing}>
               Strip Metadata
            </button>
          </div>
        </div>

        <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
          ← Back to Dashboard
        </button>
      </div>

      {/* Metadata Modal */}
      {showMetadataModal && metadata && (
        <div className="modal-overlay" onClick={() => setShowMetadataModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Image Metadata (EXIF)</h3>
              <button className="btn-close" onClick={() => setShowMetadataModal(false)}>✖</button>
            </div>
            
            <div className="modal-actions">
              <label className="toggle-label" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem' }}>
                <input type="checkbox" checked={showRawJson} onChange={(e) => setShowRawJson(e.target.checked)} />
                Show Raw JSON
              </label>
            </div>

            <div className="modal-body">
              {Object.keys(metadata).length === 0 ? (
                <p className="no-data">No EXIF metadata found in this image.</p>
              ) : showRawJson ? (
                <pre className="json-view">{JSON.stringify(metadata, null, 2)}</pre>
              ) : (
                <div className="table-container">
                  <table className="metadata-table">
                    <thead>
                      <tr>
                        <th>Tag</th>
                        <th>Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(metadata).map(([key, val]) => (
                        <tr key={key}>
                          <td className="meta-key">{key}</td>
                          <td className="meta-val">{String(val)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
