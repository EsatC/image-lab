import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import './Dashboard.css';

export default function Dashboard() {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInput = useRef(null);
  const navigate = useNavigate();

  const fetchImages = async () => {
    try {
      const { data } = await client.get('/images');
      setImages(data.images);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchImages(); }, []);

  const handleUpload = async (files) => {
    if (!files?.length) return;
    setUploading(true);
    try {
      const formData = new FormData();
      for (const file of files) formData.append('file', file);
      await client.post('/images/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      await fetchImages();
    } catch (err) {
      alert(err.response?.data?.errors?.[0] || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this image?')) return;
    try {
      await client.delete(`/images/${id}`);
      setImages((prev) => prev.filter((img) => img.id !== id));
    } catch (err) {
      alert('Delete failed.');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleUpload(e.dataTransfer.files);
  };

  const formatSize = (bytes) => {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header animate-fade-in">
        <div>
          <h1>My Images</h1>
          <p className="text-muted">{images.length} image{images.length !== 1 ? 's' : ''} uploaded</p>
        </div>
        <button className="btn btn-primary" onClick={() => fileInput.current?.click()} disabled={uploading}>
          {uploading ? <span className="spinner"></span> : '+ Upload'}
        </button>
        <input
          ref={fileInput}
          type="file"
          accept="image/*"
          multiple
          hidden
          onChange={(e) => handleUpload(e.target.files)}
        />
      </div>

      {/* Drop zone */}
      <div
        className={`drop-zone ${dragOver ? 'drop-zone--active' : ''} animate-fade-in`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInput.current?.click()}
      >
        <span className="drop-icon">📁</span>
        <p>Drag & drop images here or <span className="drop-highlight">browse</span></p>
        <p className="text-muted" style={{ fontSize: '0.8rem' }}>PNG, JPG, WEBP, BMP, TIFF — up to 16 MB</p>
      </div>

      {/* Gallery */}
      {loading ? (
        <div className="flex justify-center mt-3"><span className="spinner"></span></div>
      ) : images.length === 0 ? (
        <div className="empty-state animate-fade-in">
          <span className="empty-icon">🖼️</span>
          <p>No images yet. Upload your first image!</p>
        </div>
      ) : (
        <div className="image-grid animate-fade-in">
          {images.map((img) => (
            <div
              key={img.id}
              className="image-card card card-hover"
            >
              <div
                className="image-thumb"
                onClick={() => navigate(`/editor/${img.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <img
                  src={`${client.defaults.baseURL}/images/files/${img.filename}`}
                  alt={img.original_filename}
                  loading="lazy"
                />
              </div>
              <div className="image-info">
                <span className="image-name" title={img.original_filename}>
                  {img.original_filename}
                </span>
                <div className="image-meta">
                  <span>{img.width}×{img.height}</span>
                  <span>{formatSize(img.file_size)}</span>
                </div>
              </div>
              <div className="image-actions">
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => navigate(`/editor/${img.id}`)}
                >
                  Edit
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleDelete(img.id)}
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
