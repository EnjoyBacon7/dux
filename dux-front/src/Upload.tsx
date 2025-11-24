import React, { useRef, useState } from "react";

const Upload: React.FC = () => {
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const [uploading, setUploading] = useState(false);
    const [success, setSuccess] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSuccess(null);
        setError(null);
        const file = fileInputRef.current?.files?.[0];
        if (!file) {
            setError("Please select a file to upload.");
            return;
        }
        setUploading(true);
        try {
            const formData = new FormData();
            formData.append("file", file);
            const res = await fetch("/api/upload", {
                method: "POST",
                body: formData,
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || "Upload failed");
            }
            const data = await res.json();
            setSuccess(data.message || "File uploaded successfully!");
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Upload failed";
            setError(message);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div style={{ maxWidth: 400, margin: "2rem auto", padding: 24, border: "1px solid #eee", borderRadius: 8 }}>
            <h1 style={{ textAlign: "center" }}>Dux File Upload</h1>
            <form style={{ display: "flex", flexDirection: "column", gap: 16 }} onSubmit={handleSubmit}>
                <input
                    type="file"
                    ref={fileInputRef}
                    style={{ marginBottom: 12 }}
                    disabled={uploading}
                />
                <button type="submit" style={{ padding: "8px 0", background: uploading ? "#aaa" : "#1976d2", color: "white", border: "none", borderRadius: 4, fontWeight: 600 }} disabled={uploading}>
                    {uploading ? "Uploading..." : "Upload"}
                </button>
            </form>
            {success && <div style={{ color: 'green', marginTop: 16 }}>{success}</div>}
            {error && <div style={{ color: 'red', marginTop: 16 }}>{error}</div>}
        </div>
    );
};

export default Upload;
