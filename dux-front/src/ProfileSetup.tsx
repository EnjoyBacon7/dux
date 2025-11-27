import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./contexts/useAuth";
import { useLanguage } from "./contexts/useLanguage";
import { Header } from "./components";

interface Experience {
    company: string;
    title: string;
    startDate: string;
    endDate: string;
    isCurrent: boolean;
    description: string;
}

interface Education {
    school: string;
    degree: string;
    fieldOfStudy: string;
    startDate: string;
    endDate: string;
    description: string;
}

const ProfileSetup: React.FC = () => {
    const navigate = useNavigate();
    const { checkAuth } = useAuth();
    const { t } = useLanguage();
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    // Form state
    const [headline, setHeadline] = useState("");
    const [summary, setSummary] = useState("");
    const [location, setLocation] = useState("");
    const [skills, setSkills] = useState<string[]>([]);
    const [skillInput, setSkillInput] = useState("");
    const [experiences, setExperiences] = useState<Experience[]>([{
        company: "",
        title: "",
        startDate: "",
        endDate: "",
        isCurrent: false,
        description: ""
    }]);
    const [educations, setEducations] = useState<Education[]>([{
        school: "",
        degree: "",
        fieldOfStudy: "",
        startDate: "",
        endDate: "",
        description: ""
    }]);

    // UI state
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [step, setStep] = useState<'cv' | 'profile' | 'experience' | 'education'>('cv');

    const handleCvUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        const file = fileInputRef.current?.files?.[0];
        if (!file) {
            setError("Please select a CV file to upload.");
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
            setStep('profile');
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Upload failed";
            setError(message);
        } finally {
            setUploading(false);
        }
    };

    const handleSkillAdd = () => {
        if (skillInput.trim() && !skills.includes(skillInput.trim())) {
            setSkills([...skills, skillInput.trim()]);
            setSkillInput("");
        }
    };

    const handleSkillRemove = (skill: string) => {
        setSkills(skills.filter(s => s !== skill));
    };

    const addExperience = () => {
        setExperiences([...experiences, {
            company: "",
            title: "",
            startDate: "",
            endDate: "",
            isCurrent: false,
            description: ""
        }]);
    };

    const removeExperience = (index: number) => {
        setExperiences(experiences.filter((_, i) => i !== index));
    };

    const updateExperience = (index: number, field: keyof Experience, value: string | boolean) => {
        const updated = [...experiences];
        updated[index] = { ...updated[index], [field]: value };
        setExperiences(updated);
    };

    const addEducation = () => {
        setEducations([...educations, {
            school: "",
            degree: "",
            fieldOfStudy: "",
            startDate: "",
            endDate: "",
            description: ""
        }]);
    };

    const removeEducation = (index: number) => {
        setEducations(educations.filter((_, i) => i !== index));
    };

    const updateEducation = (index: number, field: keyof Education, value: string) => {
        const updated = [...educations];
        updated[index] = { ...updated[index], [field]: value };
        setEducations(updated);
    };

    const handleSubmit = async () => {
        setUploading(true);
        setError(null);
        try {
            const response = await fetch("/api/profile/setup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    headline,
                    summary,
                    location,
                    skills,
                    experiences: experiences.filter(exp => exp.company && exp.title),
                    educations: educations.filter(edu => edu.school && edu.degree)
                })
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || "Failed to save profile");
            }

            await checkAuth();
            navigate('/');
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to save profile";
            setError(message);
        } finally {
            setUploading(false);
        }
    };

    const skipSetup = async () => {
        navigate('/');
    };

    return (
        <>
            <Header />
            <div className="nb-page nb-stack">
                <div className="nb-card">
                    <h1 style={{ margin: '0 0 0.5rem 0' }}>{t('setup.title')}</h1>
                    <p className="nb-text-dim">{t('setup.description')}</p>

                    {/* Progress indicator */}
                    <div style={{
                        display: 'flex',
                        gap: '0.5rem',
                        marginTop: '1.5rem',
                        marginBottom: '1.5rem'
                    }}>
                        <div style={{
                            flex: 1,
                            height: '4px',
                            backgroundColor: step === 'cv' ? 'var(--nb-accent)' : 'var(--nb-fg)',
                            opacity: step === 'cv' ? 1 : 0.3,
                            borderRadius: '2px'
                        }} />
                        <div style={{
                            flex: 1,
                            height: '4px',
                            backgroundColor: step === 'profile' ? 'var(--nb-accent)' : 'var(--nb-fg)',
                            opacity: step === 'profile' ? 1 : 0.3,
                            borderRadius: '2px'
                        }} />
                        <div style={{
                            flex: 1,
                            height: '4px',
                            backgroundColor: step === 'experience' ? 'var(--nb-accent)' : 'var(--nb-fg)',
                            opacity: step === 'experience' ? 1 : 0.3,
                            borderRadius: '2px'
                        }} />
                        <div style={{
                            flex: 1,
                            height: '4px',
                            backgroundColor: step === 'education' ? 'var(--nb-accent)' : 'var(--nb-fg)',
                            opacity: step === 'education' ? 1 : 0.3,
                            borderRadius: '2px'
                        }} />
                    </div>
                </div>

                {/* Step 1: CV Upload */}
                {step === 'cv' && (
                    <div className="nb-card">
                        <h2 style={{ margin: '0 0 1rem 0' }}>{t('setup.cv_upload')}</h2>
                        <form onSubmit={handleCvUpload}>
                            <input
                                type="file"
                                ref={fileInputRef}
                                className="nb-file"
                                accept=".pdf,.doc,.docx"
                                disabled={uploading}
                            />
                            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
                                <button
                                    type="submit"
                                    className="nb-btn"
                                    disabled={uploading}
                                >
                                    {uploading ? t('upload.uploading') : t('setup.upload_cv')}
                                </button>
                                <button
                                    type="button"
                                    className="nb-btn-secondary"
                                    onClick={() => setStep('profile')}
                                >
                                    {t('setup.skip_cv')}
                                </button>
                            </div>
                        </form>
                        {error && <div className="nb-alert nb-alert--danger" style={{ marginTop: '1rem' }}>{error}</div>}
                    </div>
                )}

                {/* Step 2: Profile Information */}
                {step === 'profile' && (
                    <div className="nb-card">
                        <h2 style={{ margin: '0 0 1rem 0' }}>{t('setup.profile_info')}</h2>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <div>
                                <label className="nb-label">{t('setup.headline')}</label>
                                <input
                                    type="text"
                                    className="nb-input"
                                    value={headline}
                                    onChange={(e) => setHeadline(e.target.value)}
                                    placeholder="e.g., Senior Software Engineer"
                                />
                            </div>
                            <div>
                                <label className="nb-label">{t('setup.location')}</label>
                                <input
                                    type="text"
                                    className="nb-input"
                                    value={location}
                                    onChange={(e) => setLocation(e.target.value)}
                                    placeholder="e.g., San Francisco, CA"
                                />
                            </div>
                            <div>
                                <label className="nb-label">{t('setup.summary')}</label>
                                <textarea
                                    className="nb-input"
                                    value={summary}
                                    onChange={(e) => setSummary(e.target.value)}
                                    rows={4}
                                    placeholder={t('setup.summary_placeholder')}
                                />
                            </div>
                            <div>
                                <label className="nb-label">{t('setup.skills')}</label>
                                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                    <input
                                        type="text"
                                        className="nb-input"
                                        value={skillInput}
                                        onChange={(e) => setSkillInput(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleSkillAdd())}
                                        placeholder="e.g., React, Python, etc."
                                        style={{ flex: 1 }}
                                    />
                                    <button
                                        type="button"
                                        className="nb-btn-secondary"
                                        onClick={handleSkillAdd}
                                    >
                                        {t('setup.add_skill')}
                                    </button>
                                </div>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    {skills.map((skill, idx) => (
                                        <span
                                            key={idx}
                                            style={{
                                                padding: '0.25rem 0.75rem',
                                                backgroundColor: 'var(--nb-accent)',
                                                border: 'var(--nb-border) solid var(--nb-fg)',
                                                borderRadius: '4px',
                                                fontSize: '0.875rem',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '0.5rem'
                                            }}
                                        >
                                            {skill}
                                            <button
                                                onClick={() => handleSkillRemove(skill)}
                                                style={{
                                                    background: 'none',
                                                    border: 'none',
                                                    cursor: 'pointer',
                                                    padding: 0,
                                                    fontSize: '1rem',
                                                    lineHeight: 1
                                                }}
                                            >
                                                ×
                                            </button>
                                        </span>
                                    ))}
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                                <button
                                    type="button"
                                    className="nb-btn"
                                    onClick={() => setStep('experience')}
                                >
                                    {t('setup.next')}
                                </button>
                                <button
                                    type="button"
                                    className="nb-btn-secondary"
                                    onClick={() => setStep('cv')}
                                >
                                    {t('setup.back')}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 3: Work Experience */}
                {step === 'experience' && (
                    <div className="nb-card">
                        <h2 style={{ margin: '0 0 1rem 0' }}>{t('setup.experience')}</h2>
                        {experiences.map((exp, idx) => (
                            <div
                                key={idx}
                                style={{
                                    marginBottom: '1.5rem',
                                    padding: '1rem',
                                    border: 'var(--nb-border) solid var(--nb-fg)',
                                    borderRadius: '6px'
                                }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                    <h3 style={{ margin: 0, fontSize: '1rem' }}>Experience #{idx + 1}</h3>
                                    {experiences.length > 1 && (
                                        <button
                                            type="button"
                                            onClick={() => removeExperience(idx)}
                                            className="nb-btn-secondary"
                                            style={{ fontSize: '0.875rem' }}
                                        >
                                            {t('setup.remove')}
                                        </button>
                                    )}
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                    <input
                                        type="text"
                                        className="nb-input"
                                        placeholder={t('setup.company')}
                                        value={exp.company}
                                        onChange={(e) => updateExperience(idx, 'company', e.target.value)}
                                    />
                                    <input
                                        type="text"
                                        className="nb-input"
                                        placeholder={t('setup.job_title')}
                                        value={exp.title}
                                        onChange={(e) => updateExperience(idx, 'title', e.target.value)}
                                    />
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                                        <input
                                            type="month"
                                            className="nb-input"
                                            placeholder={t('setup.start_date')}
                                            value={exp.startDate}
                                            onChange={(e) => updateExperience(idx, 'startDate', e.target.value)}
                                        />
                                        <input
                                            type="month"
                                            className="nb-input"
                                            placeholder={t('setup.end_date')}
                                            value={exp.endDate}
                                            onChange={(e) => updateExperience(idx, 'endDate', e.target.value)}
                                            disabled={exp.isCurrent}
                                        />
                                    </div>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
                                        <input
                                            type="checkbox"
                                            checked={exp.isCurrent}
                                            onChange={(e) => updateExperience(idx, 'isCurrent', e.target.checked)}
                                        />
                                        {t('setup.current_position')}
                                    </label>
                                    <textarea
                                        className="nb-input"
                                        placeholder={t('setup.job_description')}
                                        value={exp.description}
                                        onChange={(e) => updateExperience(idx, 'description', e.target.value)}
                                        rows={3}
                                    />
                                </div>
                            </div>
                        ))}
                        <button
                            type="button"
                            className="nb-btn-secondary"
                            onClick={addExperience}
                            style={{ marginBottom: '1rem' }}
                        >
                            {t('setup.add_experience')}
                        </button>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button
                                type="button"
                                className="nb-btn"
                                onClick={() => setStep('education')}
                            >
                                {t('setup.next')}
                            </button>
                            <button
                                type="button"
                                className="nb-btn-secondary"
                                onClick={() => setStep('profile')}
                            >
                                {t('setup.back')}
                            </button>
                        </div>
                    </div>
                )}

                {/* Step 4: Education */}
                {step === 'education' && (
                    <div className="nb-card">
                        <h2 style={{ margin: '0 0 1rem 0' }}>{t('setup.education')}</h2>
                        {educations.map((edu, idx) => (
                            <div
                                key={idx}
                                style={{
                                    marginBottom: '1.5rem',
                                    padding: '1rem',
                                    border: 'var(--nb-border) solid var(--nb-fg)',
                                    borderRadius: '6px'
                                }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                    <h3 style={{ margin: 0, fontSize: '1rem' }}>Education #{idx + 1}</h3>
                                    {educations.length > 1 && (
                                        <button
                                            type="button"
                                            onClick={() => removeEducation(idx)}
                                            className="nb-btn-secondary"
                                            style={{ fontSize: '0.875rem' }}
                                        >
                                            {t('setup.remove')}
                                        </button>
                                    )}
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                    <input
                                        type="text"
                                        className="nb-input"
                                        placeholder={t('setup.school')}
                                        value={edu.school}
                                        onChange={(e) => updateEducation(idx, 'school', e.target.value)}
                                    />
                                    <input
                                        type="text"
                                        className="nb-input"
                                        placeholder={t('setup.degree')}
                                        value={edu.degree}
                                        onChange={(e) => updateEducation(idx, 'degree', e.target.value)}
                                    />
                                    <input
                                        type="text"
                                        className="nb-input"
                                        placeholder={t('setup.field_of_study')}
                                        value={edu.fieldOfStudy}
                                        onChange={(e) => updateEducation(idx, 'fieldOfStudy', e.target.value)}
                                    />
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                                        <input
                                            type="month"
                                            className="nb-input"
                                            placeholder={t('setup.start_date')}
                                            value={edu.startDate}
                                            onChange={(e) => updateEducation(idx, 'startDate', e.target.value)}
                                        />
                                        <input
                                            type="month"
                                            className="nb-input"
                                            placeholder={t('setup.end_date')}
                                            value={edu.endDate}
                                            onChange={(e) => updateEducation(idx, 'endDate', e.target.value)}
                                        />
                                    </div>
                                    <textarea
                                        className="nb-input"
                                        placeholder={t('setup.education_description')}
                                        value={edu.description}
                                        onChange={(e) => updateEducation(idx, 'description', e.target.value)}
                                        rows={2}
                                    />
                                </div>
                            </div>
                        ))}
                        <button
                            type="button"
                            className="nb-btn-secondary"
                            onClick={addEducation}
                            style={{ marginBottom: '1rem' }}
                        >
                            {t('setup.add_education')}
                        </button>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button
                                type="button"
                                className="nb-btn"
                                onClick={handleSubmit}
                                disabled={uploading}
                            >
                                {uploading ? t('setup.saving') : t('setup.complete')}
                            </button>
                            <button
                                type="button"
                                className="nb-btn-secondary"
                                onClick={() => setStep('experience')}
                            >
                                {t('setup.back')}
                            </button>
                        </div>
                        {error && <div className="nb-alert nb-alert--danger" style={{ marginTop: '1rem' }}>{error}</div>}
                    </div>
                )}

                {/* Skip Setup */}
                <div className="nb-card" style={{ textAlign: 'center' }}>
                    <button
                        type="button"
                        className="nb-btn-ghost"
                        onClick={skipSetup}
                    >
                        {t('setup.skip_for_now')}
                    </button>
                </div>
            </div>
        </>
    );
};

export default ProfileSetup;
