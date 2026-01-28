import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "./index";
import { useLanguage } from "../contexts/useLanguage";
import "../styles/detailedAnalysis.module.css";

// ============================================================================
// Type Definitions
// ============================================================================

interface ScoreDimension {
    score: number;
    justification: string;
    evidence: string[];
}

interface FullScores {
    overall_score: number;
    overall_summary: string;
    completeness: ScoreDimension;
    experience_quality: ScoreDimension;
    skills_relevance: ScoreDimension;
    impact_evidence: ScoreDimension;
    clarity: ScoreDimension;
    consistency: ScoreDimension;
    strengths: string[];
    weaknesses: string[];
    missing_info: string[];
    red_flags: string[];
    recommendations: string[];
}

interface PersonalInfo {
    name?: string;
    email?: string;
    phone?: string;
    location?: string;
    linkedin_url?: string;
    portfolio_url?: string;
}

interface WorkExperience {
    role: string;
    company: string;
    start_date?: string;
    end_date?: string;
    is_current: boolean;
    location?: string;
    responsibilities: string[];
}

interface Education {
    degree: string;
    field_of_study?: string;
    institution: string;
    start_date?: string;
    end_date?: string;
    gpa?: string;
    honors?: string;
}

interface SkillCategory {
    category?: string;
    skills: string[];
}

interface Project {
    name: string;
    description?: string;
    technologies: string[];
    url?: string;
    date?: string;
}

interface Certification {
    name: string;
    issuer?: string;
    date?: string;
    credential_id?: string;
}

interface Language {
    language: string;
    proficiency?: string;
}

interface StructuredCV {
    personal_info: PersonalInfo;
    professional_summary?: string;
    work_experience: WorkExperience[];
    education: Education[];
    skills: SkillCategory[];
    projects: Project[];
    certifications: Certification[];
    languages: Language[];
}

interface TimelineGap {
    start_date: string;
    end_date: string;
    duration_months: number;
    between_jobs: string[];
}

interface TimelineOverlap {
    job1: string;
    job2: string;
    overlap_start: string;
    overlap_end: string;
    overlap_months: number;
}

interface DateIssue {
    section: string;
    issue_type: string;
    description: string;
}

interface DerivedFeatures {
    total_experience_months?: number;
    total_experience_years?: number;
    experience_count: number;
    education_count: number;
    skills_count: number;
    projects_count: number;
    certifications_count: number;
    has_quantified_results: boolean;
    quantified_results_count: number;
    quantified_examples: string[];
    timeline_gaps: TimelineGap[];
    timeline_overlaps: TimelineOverlap[];
    date_issues: DateIssue[];
    avg_tenure_months?: number;
    shortest_tenure_months?: number;
    longest_tenure_months?: number;
    job_hopping_flag: boolean;
    missing_sections: string[];
    has_contact_info: boolean;
    has_summary: boolean;
    has_experience: boolean;
    has_education: boolean;
    has_skills: boolean;
}

interface VisualAnalysis {
    visual_strengths: string[];
    visual_weaknesses: string[];
    visual_recommendations: string[];
    layout_assessment?: string;
    typography_assessment?: string;
    readability_assessment?: string;
    image_quality_notes: string[];
}

interface DetailedEvaluation {
    id: number;
    cv_filename?: string;
    created_at?: string;
    evaluation_status?: string;
    error_message?: string;
    full_scores?: FullScores;
    structured_cv?: StructuredCV;
    derived_features?: DerivedFeatures;
    visual_analysis?: VisualAnalysis;
}

// ============================================================================
// Component
// ============================================================================

const DetailedAnalysis: React.FC = () => {
    const { t } = useLanguage();
    const navigate = useNavigate();
    const [evaluation, setEvaluation] = useState<DetailedEvaluation | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isContentExpanded, setIsContentExpanded] = useState(true);
    const [isVisualExpanded, setIsVisualExpanded] = useState(true);

    useEffect(() => {
        const fetchEvaluation = async () => {
            try {
                const response = await fetch("/api/cv/evaluation/detailed", {
                    credentials: "include",
                });

                if (response.ok) {
                    const data = await response.json();
                    setEvaluation(data);
                } else if (response.status === 404) {
                    setError(t("detailed_analysis.no_evaluation"));
                } else if (response.status === 400) {
                    const errorData = await response.json();
                    setError(errorData.detail || t("detailed_analysis.error"));
                } else {
                    setError(t("detailed_analysis.error"));
                }
            } catch {
                setError(t("detailed_analysis.error"));
            } finally {
                setIsLoading(false);
            }
        };

        fetchEvaluation();
    }, [t]);

    const handleBack = () => {
        navigate("/profile-hub");
    };

    // Get score color based on value
    const getScoreColor = (score: number): string => {
        if (score < 50) return "var(--nb-danger)";
        if (score < 70) return "var(--nb-warning)";
        return "var(--nb-success)";
    };

    // Calculate SVG circle parameters
    const circleRadius = 45;
    const circumference = 2 * Math.PI * circleRadius;

    // Render loading state
    if (isLoading) {
        return (
            <>
                <Header />
                <main className="nb-page detailed-analysis-container">
                    <div className="detailed-analysis-loading">
                        <div className="detailed-analysis-spinner"></div>
                        <p>{t("detailed_analysis.loading")}</p>
                    </div>
                </main>
            </>
        );
    }

    // Render error state
    if (error) {
        return (
            <>
                <Header />
                <main className="nb-page detailed-analysis-container">
                    <div className="detailed-analysis-error">
                        <p>{error}</p>
                        <button className="nb-btn nb-btn--accent" onClick={handleBack}>
                            {t("detailed_analysis.back")}
                        </button>
                    </div>
                </main>
            </>
        );
    }

    if (!evaluation) {
        return null;
    }

    const { full_scores, structured_cv, derived_features, visual_analysis } = evaluation;
    const scorePercent = full_scores?.overall_score ?? 0;
    const strokeDashoffset = circumference - (scorePercent / 100) * circumference;

    // Format field name to user-friendly label
    const formatFieldName = (fieldName: string): string => {
        const fieldMap: { [key: string]: string } = {
            personal_info: t("detailed_analysis.personal_info"),
            professional_summary: t("detailed_analysis.professional_summary"),
            work_experience: t("detailed_analysis.work_experience"),
            education: t("detailed_analysis.education"),
            skills: t("detailed_analysis.skills"),
            projects: t("detailed_analysis.projects"),
            certifications: t("detailed_analysis.certifications"),
            languages: t("detailed_analysis.languages"),
            date_issues: t("detailed_analysis.date_issues"),
            validation_warnings: t("detailed_analysis.validation_warnings"),
            timeline_gaps: t("detailed_analysis.timeline_gaps"),
            timeline_overlaps: t("detailed_analysis.timeline_overlaps"),
        };
        
        return fieldMap[fieldName] || fieldName.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
    };

    // Format evidence string to user-friendly description
    const formatEvidence = (evidenceStr: string): string => {
        // Handle array references like "work_experience[0]"
        const arrayMatch = evidenceStr.match(/^(\w+)\[(\d+)\]$/);
        if (arrayMatch) {
            const [, fieldName, index] = arrayMatch;
            const idx = parseInt(index, 10);
            
            // Try to get actual data from structured_cv
            if (structured_cv) {
                if (fieldName === "work_experience" && structured_cv.work_experience[idx]) {
                    const exp = structured_cv.work_experience[idx];
                    return `${exp.role} at ${exp.company}`;
                }
                if (fieldName === "education" && structured_cv.education[idx]) {
                    const edu = structured_cv.education[idx];
                    return `${edu.degree} at ${edu.institution}`;
                }
                if (fieldName === "skills" && structured_cv.skills[idx]) {
                    const skill = structured_cv.skills[idx];
                    const category = skill.category || t("detailed_analysis.skills");
                    return `${category}: ${skill.skills.slice(0, 3).join(", ")}${skill.skills.length > 3 ? "..." : ""}`;
                }
                if (fieldName === "projects" && structured_cv.projects[idx]) {
                    return structured_cv.projects[idx].name;
                }
                if (fieldName === "certifications" && structured_cv.certifications[idx]) {
                    return structured_cv.certifications[idx].name;
                }
            }
            
            // Fallback: format as "First/Second/Third..." item
            const ordinals = [
                t("detailed_analysis.first"),
                t("detailed_analysis.second"),
                t("detailed_analysis.third"),
                t("detailed_analysis.fourth"),
                t("detailed_analysis.fifth"),
            ];
            const ordinal = ordinals[idx] || `${idx + 1}${t("detailed_analysis.ordinal_suffix")}`;
            const fieldLabel = formatFieldName(fieldName);
            return `${ordinal} ${fieldLabel}`;
        }
        
        // Handle simple field names
        return formatFieldName(evidenceStr);
    };

    // Dimension scores for detailed display
    const dimensionScores = full_scores ? [
        { key: "completeness", label: t("cv_score.completeness"), data: full_scores.completeness },
        { key: "experience", label: t("cv_score.experience"), data: full_scores.experience_quality },
        { key: "skills", label: t("cv_score.skills"), data: full_scores.skills_relevance },
        { key: "impact", label: t("cv_score.impact"), data: full_scores.impact_evidence },
        { key: "clarity", label: t("cv_score.clarity"), data: full_scores.clarity },
        { key: "consistency", label: t("cv_score.consistency"), data: full_scores.consistency },
    ] : [];

    return (
        <>
            <Header />
            <main className="nb-page detailed-analysis-container">
                <div className="detailed-analysis-content">
                    {/* Back Button & Header */}
                    <div className="detailed-analysis-header">
                        <button className="detailed-analysis-back-btn" onClick={handleBack}>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M19 12H5M12 19l-7-7 7-7" />
                            </svg>
                            {t("detailed_analysis.back")}
                        </button>
                        <div className="detailed-analysis-header-info">
                            <h1 className="detailed-analysis-title">{t("detailed_analysis.title")}</h1>
                            {evaluation.cv_filename && (
                                <span className="detailed-analysis-filename">{evaluation.cv_filename}</span>
                            )}
                        </div>
                    </div>

                    {/* ============================================== */}
                    {/* SECTION 1: CONTENT ANALYSIS */}
                    {/* ============================================== */}
                    <section className="detailed-analysis-section content-section">
                        <h2 
                            className="section-title section-title--clickable"
                            onClick={() => setIsContentExpanded(!isContentExpanded)}
                            role="button"
                            tabIndex={0}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar' || e.code === 'Space') {
                                    if (e.key === ' ' || e.key === 'Spacebar' || e.code === 'Space') {
                                        e.preventDefault();
                                    }
                                    setIsContentExpanded(!isContentExpanded);
                                }
                            }}
                        >
                            <span>{t("detailed_analysis.content_analysis")}</span>
                            <svg 
                                className={`section-chevron ${isContentExpanded ? 'expanded' : ''}`}
                                viewBox="0 0 24 24" 
                                fill="none" 
                                stroke="currentColor" 
                                strokeWidth="2"
                            >
                                <path d="M6 9l6 6 6-6" />
                            </svg>
                        </h2>
                        {isContentExpanded && (
                        <div className="section-content">

                        {/* Overall Score Card */}
                        {full_scores && (
                            <div className="nb-card detailed-card overall-score-card">
                                <h3 className="card-title">{t("detailed_analysis.overall_score")}</h3>
                                <div className="overall-score-content">
                                    <div className="score-circle-container">
                                        <svg className="score-circle" viewBox="0 0 100 100">
                                            <circle
                                                cx="50"
                                                cy="50"
                                                r={circleRadius}
                                                fill="none"
                                                stroke="var(--nb-bg-muted)"
                                                strokeWidth="8"
                                            />
                                            <circle
                                                cx="50"
                                                cy="50"
                                                r={circleRadius}
                                                fill="none"
                                                stroke={getScoreColor(scorePercent)}
                                                strokeWidth="8"
                                                strokeLinecap="round"
                                                strokeDasharray={circumference}
                                                strokeDashoffset={strokeDashoffset}
                                                transform="rotate(-90 50 50)"
                                                className="score-circle-progress"
                                            />
                                            <text
                                                x="50"
                                                y="50"
                                                textAnchor="middle"
                                                dy="0.35em"
                                                className="score-text"
                                            >
                                                {scorePercent}
                                            </text>
                                        </svg>
                                    </div>
                                    <div className="overall-summary">
                                        <p>{full_scores.overall_summary}</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Score Dimensions */}
                        {dimensionScores.length > 0 && (
                            <div className="nb-card detailed-card dimensions-card">
                                <h3 className="card-title">{t("detailed_analysis.dimensions")}</h3>
                                <div className="dimensions-list">
                                    {dimensionScores.map(({ key, label, data }) => (
                                        <div key={key} className="dimension-item">
                                            <div className="dimension-header">
                                                <span className="dimension-label">{label}</span>
                                                <span
                                                    className="dimension-value"
                                                    style={{ color: getScoreColor(data.score) }}
                                                >
                                                    {data.score}
                                                </span>
                                            </div>
                                            <div className="dimension-bar-bg">
                                                <div
                                                    className="dimension-bar-fill"
                                                    style={{
                                                        width: `${data.score}%`,
                                                        backgroundColor: getScoreColor(data.score),
                                                    }}
                                                />
                                            </div>
                                            <p className="dimension-justification">{data.justification}</p>
                                            {data.evidence.length > 0 && (
                                                <div className="dimension-evidence">
                                                    <span className="evidence-label">{t("detailed_analysis.evidence")}:</span>
                                                    <ul>
                                                        {data.evidence.map((e, i) => (
                                                            <li key={i}>{formatEvidence(e)}</li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Content Strengths & Weaknesses */}
                        {full_scores && (full_scores.strengths.length > 0 || full_scores.weaknesses.length > 0) && (
                            <div className="strengths-weaknesses-row">
                                {full_scores.strengths.length > 0 && (
                                    <div className="nb-card detailed-card strengths-card">
                                        <h3 className="card-title">{t("detailed_analysis.content_strengths")}</h3>
                                        <ul className="feedback-list strengths">
                                            {full_scores.strengths.map((s, i) => (
                                                <li key={i}>{s}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {full_scores.weaknesses.length > 0 && (
                                    <div className="nb-card detailed-card weaknesses-card">
                                        <h3 className="card-title">{t("detailed_analysis.content_weaknesses")}</h3>
                                        <ul className="feedback-list weaknesses">
                                            {full_scores.weaknesses.map((w, i) => (
                                                <li key={i}>{w}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Content Recommendations */}
                        {full_scores && full_scores.recommendations.length > 0 && (
                            <div className="nb-card detailed-card recommendations-card">
                                <h3 className="card-title">{t("detailed_analysis.content_recommendations")}</h3>
                                <ul className="recommendations-list">
                                    {full_scores.recommendations.map((r, i) => (
                                        <li key={i}>{r}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Red Flags & Missing Info */}
                        {full_scores && (full_scores.red_flags.length > 0 || full_scores.missing_info.length > 0) && (
                            <div className="alerts-row">
                                {full_scores.red_flags.length > 0 && (
                                    <div className="nb-card detailed-card red-flags-card">
                                        <h3 className="card-title">{t("detailed_analysis.red_flags")}</h3>
                                        <ul className="feedback-list red-flags">
                                            {full_scores.red_flags.map((f, i) => (
                                                <li key={i}>{f}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {full_scores.missing_info.length > 0 && (
                                    <div className="nb-card detailed-card missing-info-card">
                                        <h3 className="card-title">{t("detailed_analysis.missing_info")}</h3>
                                        <ul className="feedback-list missing">
                                            {full_scores.missing_info.map((m, i) => (
                                                <li key={i}>{m}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Structured CV Data */}
                        {structured_cv && (
                            <div className="nb-card detailed-card structured-cv-card">
                                <h3 className="card-title">{t("detailed_analysis.structured_cv")}</h3>

                                {/* Personal Info */}
                                {structured_cv.personal_info && (
                                    <div className="cv-section personal-info-section">
                                        <h4>{t("detailed_analysis.personal_info")}</h4>
                                        <div className="personal-info-grid">
                                            {structured_cv.personal_info.name && (
                                                <div className="info-item">
                                                    <span className="info-label">{t("detailed_analysis.name")}:</span>
                                                    <span>{structured_cv.personal_info.name}</span>
                                                </div>
                                            )}
                                            {structured_cv.personal_info.email && (
                                                <div className="info-item">
                                                    <span className="info-label">{t("detailed_analysis.email")}:</span>
                                                    <span>{structured_cv.personal_info.email}</span>
                                                </div>
                                            )}
                                            {structured_cv.personal_info.phone && (
                                                <div className="info-item">
                                                    <span className="info-label">{t("detailed_analysis.phone")}:</span>
                                                    <span>{structured_cv.personal_info.phone}</span>
                                                </div>
                                            )}
                                            {structured_cv.personal_info.location && (
                                                <div className="info-item">
                                                    <span className="info-label">{t("detailed_analysis.location")}:</span>
                                                    <span>{structured_cv.personal_info.location}</span>
                                                </div>
                                            )}
                                            {structured_cv.personal_info.linkedin_url && (
                                                <div className="info-item">
                                                    <span className="info-label">LinkedIn:</span>
                                                    <a href={structured_cv.personal_info.linkedin_url} target="_blank" rel="noopener noreferrer">
                                                        {structured_cv.personal_info.linkedin_url}
                                                    </a>
                                                </div>
                                            )}
                                            {structured_cv.personal_info.portfolio_url && (
                                                <div className="info-item">
                                                    <span className="info-label">{t("detailed_analysis.portfolio")}:</span>
                                                    <a href={structured_cv.personal_info.portfolio_url} target="_blank" rel="noopener noreferrer">
                                                        {structured_cv.personal_info.portfolio_url}
                                                    </a>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Professional Summary */}
                                {structured_cv.professional_summary && (
                                    <div className="cv-section summary-section">
                                        <h4>{t("detailed_analysis.professional_summary")}</h4>
                                        <p>{structured_cv.professional_summary}</p>
                                    </div>
                                )}

                                {/* Work Experience */}
                                {structured_cv.work_experience.length > 0 && (
                                    <div className="cv-section experience-section">
                                        <h4>{t("detailed_analysis.work_experience")}</h4>
                                        {structured_cv.work_experience.map((exp, i) => (
                                            <div key={i} className="experience-item">
                                                <div className="experience-header">
                                                    <strong>{exp.role}</strong>
                                                    <span className="experience-company">{exp.company}</span>
                                                </div>
                                                <div className="experience-meta">
                                                    {exp.start_date && (
                                                        <span>
                                                            {exp.start_date} - {exp.is_current ? t("detailed_analysis.present") : exp.end_date}
                                                        </span>
                                                    )}
                                                    {exp.location && <span>{exp.location}</span>}
                                                </div>
                                                {exp.responsibilities.length > 0 && (
                                                    <ul className="responsibilities">
                                                        {exp.responsibilities.map((r, j) => (
                                                            <li key={j}>{r}</li>
                                                        ))}
                                                    </ul>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Education */}
                                {structured_cv.education.length > 0 && (
                                    <div className="cv-section education-section">
                                        <h4>{t("detailed_analysis.education")}</h4>
                                        {structured_cv.education.map((edu, i) => (
                                            <div key={i} className="education-item">
                                                <strong>{edu.degree}</strong>
                                                {edu.field_of_study && <span> in {edu.field_of_study}</span>}
                                                <div className="education-meta">
                                                    <span>{edu.institution}</span>
                                                    {edu.start_date && (
                                                        <span> | {edu.start_date} - {edu.end_date}</span>
                                                    )}
                                                    {edu.gpa && <span> | GPA: {edu.gpa}</span>}
                                                    {edu.honors && <span> | {edu.honors}</span>}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Skills */}
                                {structured_cv.skills.length > 0 && (
                                    <div className="cv-section skills-section">
                                        <h4>{t("detailed_analysis.skills")}</h4>
                                        {structured_cv.skills.map((cat, i) => (
                                            <div key={i} className="skill-category">
                                                {cat.category && <span className="category-name">{cat.category}: </span>}
                                                <span className="skill-list">{cat.skills.join(", ")}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Projects */}
                                {structured_cv.projects.length > 0 && (
                                    <div className="cv-section projects-section">
                                        <h4>{t("detailed_analysis.projects")}</h4>
                                        {structured_cv.projects.map((proj, i) => (
                                            <div key={i} className="project-item">
                                                <strong>{proj.name}</strong>
                                                {proj.date && <span className="project-date"> ({proj.date})</span>}
                                                {proj.description && <p>{proj.description}</p>}
                                                {proj.technologies.length > 0 && (
                                                    <div className="project-tech">
                                                        {proj.technologies.map((tech, j) => (
                                                            <span key={j} className="tech-tag">{tech}</span>
                                                        ))}
                                                    </div>
                                                )}
                                                {proj.url && (
                                                    <a href={proj.url} target="_blank" rel="noopener noreferrer">
                                                        {proj.url}
                                                    </a>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Certifications */}
                                {structured_cv.certifications.length > 0 && (
                                    <div className="cv-section certifications-section">
                                        <h4>{t("detailed_analysis.certifications")}</h4>
                                        {structured_cv.certifications.map((cert, i) => (
                                            <div key={i} className="certification-item">
                                                <strong>{cert.name}</strong>
                                                {cert.issuer && <span> - {cert.issuer}</span>}
                                                {cert.date && <span> ({cert.date})</span>}
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Languages */}
                                {structured_cv.languages.length > 0 && (
                                    <div className="cv-section languages-section">
                                        <h4>{t("detailed_analysis.languages")}</h4>
                                        <div className="languages-list">
                                            {structured_cv.languages.map((lang, i) => (
                                                <span key={i} className="language-item">
                                                    {lang.language}
                                                    {lang.proficiency && ` (${lang.proficiency})`}
                                                    {i < structured_cv.languages.length - 1 && ", "}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Derived Features */}
                        {derived_features && (
                            <div className="nb-card detailed-card derived-features-card">
                                <h3 className="card-title">{t("detailed_analysis.derived_features")}</h3>

                                {/* Experience Metrics */}
                                <div className="derived-section metrics-section">
                                    <h4>{t("detailed_analysis.experience_metrics")}</h4>
                                    <div className="metrics-grid">
                                        {derived_features.total_experience_years != null && (
                                            <div className="metric-item">
                                                <span className="metric-value">{derived_features.total_experience_years.toFixed(1)}</span>
                                                <span className="metric-label">{t("detailed_analysis.years_experience")}</span>
                                            </div>
                                        )}
                                        <div className="metric-item">
                                            <span className="metric-value">{derived_features.experience_count}</span>
                                            <span className="metric-label">{t("detailed_analysis.positions")}</span>
                                        </div>
                                        <div className="metric-item">
                                            <span className="metric-value">{derived_features.education_count}</span>
                                            <span className="metric-label">{t("detailed_analysis.education_entries")}</span>
                                        </div>
                                        <div className="metric-item">
                                            <span className="metric-value">{derived_features.skills_count}</span>
                                            <span className="metric-label">{t("detailed_analysis.skills_count")}</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Quantified Results */}
                                {derived_features.has_quantified_results && (
                                    <div className="derived-section quantified-section">
                                        <h4>{t("detailed_analysis.quantified_results")}</h4>
                                        <p className="quantified-count">
                                            {t("detailed_analysis.quantified_count")}: {derived_features.quantified_results_count}
                                        </p>
                                        {derived_features.quantified_examples.length > 0 && (
                                            <ul className="quantified-examples">
                                                {derived_features.quantified_examples.map((ex, i) => (
                                                    <li key={i}>{ex}</li>
                                                ))}
                                            </ul>
                                        )}
                                    </div>
                                )}

                                {/* Timeline Gaps */}
                                {derived_features.timeline_gaps.length > 0 && (
                                    <div className="derived-section timeline-section">
                                        <h4>{t("detailed_analysis.timeline_gaps")}</h4>
                                        <div className="timeline-items">
                                            {derived_features.timeline_gaps.map((gap, i) => (
                                                <div key={i} className="timeline-gap-item">
                                                    <span className="gap-duration">{gap.duration_months} {t("detailed_analysis.months")}</span>
                                                    <span className="gap-dates">{gap.start_date} - {gap.end_date}</span>
                                                    {gap.between_jobs.length > 0 && (
                                                        <span className="gap-between">
                                                            {t("detailed_analysis.between")}: {gap.between_jobs.join(" → ")}
                                                        </span>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Tenure Analysis */}
                                {derived_features.avg_tenure_months != null && (
                                    <div className="derived-section tenure-section">
                                        <h4>{t("detailed_analysis.tenure_analysis")}</h4>
                                        <div className="tenure-grid">
                                            <div className="tenure-item">
                                                <span className="tenure-label">{t("detailed_analysis.avg_tenure")}:</span>
                                                <span>{derived_features.avg_tenure_months.toFixed(1)} {t("detailed_analysis.months")}</span>
                                            </div>
                                            {derived_features.shortest_tenure_months != null && (
                                                <div className="tenure-item">
                                                    <span className="tenure-label">{t("detailed_analysis.shortest_tenure")}:</span>
                                                    <span>{derived_features.shortest_tenure_months} {t("detailed_analysis.months")}</span>
                                                </div>
                                            )}
                                            {derived_features.longest_tenure_months != null && (
                                                <div className="tenure-item">
                                                    <span className="tenure-label">{t("detailed_analysis.longest_tenure")}:</span>
                                                    <span>{derived_features.longest_tenure_months} {t("detailed_analysis.months")}</span>
                                                </div>
                                            )}
                                            {derived_features.job_hopping_flag && (
                                                <div className="tenure-item job-hopping">
                                                    <span className="warning-badge">{t("detailed_analysis.job_hopping_warning")}</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Completeness Flags */}
                                <div className="derived-section completeness-section">
                                    <h4>{t("detailed_analysis.completeness_flags")}</h4>
                                    <div className="completeness-grid">
                                        <span className={`flag ${derived_features.has_contact_info ? "present" : "missing"}`}>
                                            {derived_features.has_contact_info ? "✓" : "✗"} {t("detailed_analysis.contact_info")}
                                        </span>
                                        <span className={`flag ${derived_features.has_summary ? "present" : "missing"}`}>
                                            {derived_features.has_summary ? "✓" : "✗"} {t("detailed_analysis.summary")}
                                        </span>
                                        <span className={`flag ${derived_features.has_experience ? "present" : "missing"}`}>
                                            {derived_features.has_experience ? "✓" : "✗"} {t("detailed_analysis.experience")}
                                        </span>
                                        <span className={`flag ${derived_features.has_education ? "present" : "missing"}`}>
                                            {derived_features.has_education ? "✓" : "✗"} {t("detailed_analysis.education_flag")}
                                        </span>
                                        <span className={`flag ${derived_features.has_skills ? "present" : "missing"}`}>
                                            {derived_features.has_skills ? "✓" : "✗"} {t("detailed_analysis.skills_flag")}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}
                        </div>
                        )}
                    </section>

                    {/* ============================================== */}
                    {/* SECTION 2: VISUAL ANALYSIS */}
                    {/* ============================================== */}
                    {visual_analysis && (
                        <section className="detailed-analysis-section visual-section">
                            <h2 
                                className="section-title section-title--clickable"
                                onClick={() => setIsVisualExpanded(!isVisualExpanded)}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar' || e.code === 'Space') {
                                        if (e.key === ' ' || e.key === 'Spacebar' || e.code === 'Space') {
                                            e.preventDefault();
                                        }
                                        setIsVisualExpanded(!isVisualExpanded);
                                    }
                                }}
                            >
                                <span>{t("detailed_analysis.visual_analysis")}</span>
                                <svg 
                                    className={`section-chevron ${isVisualExpanded ? 'expanded' : ''}`}
                                    viewBox="0 0 24 24" 
                                    fill="none" 
                                    stroke="currentColor" 
                                    strokeWidth="2"
                                >
                                    <path d="M6 9l6 6 6-6" />
                                </svg>
                            </h2>
                            {isVisualExpanded && (
                            <div className="section-content">

                            {/* Visual Strengths & Weaknesses */}
                            {(visual_analysis.visual_strengths.length > 0 || visual_analysis.visual_weaknesses.length > 0) && (
                                <div className="strengths-weaknesses-row">
                                    {visual_analysis.visual_strengths.length > 0 && (
                                        <div className="nb-card detailed-card strengths-card visual">
                                            <h3 className="card-title">{t("detailed_analysis.visual_strengths")}</h3>
                                            <ul className="feedback-list strengths">
                                                {visual_analysis.visual_strengths.map((s, i) => (
                                                    <li key={i}>{s}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    {visual_analysis.visual_weaknesses.length > 0 && (
                                        <div className="nb-card detailed-card weaknesses-card visual">
                                            <h3 className="card-title">{t("detailed_analysis.visual_weaknesses")}</h3>
                                            <ul className="feedback-list weaknesses">
                                                {visual_analysis.visual_weaknesses.map((w, i) => (
                                                    <li key={i}>{w}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Visual Recommendations */}
                            {visual_analysis.visual_recommendations.length > 0 && (
                                <div className="nb-card detailed-card recommendations-card visual">
                                    <h3 className="card-title">{t("detailed_analysis.visual_recommendations")}</h3>
                                    <ul className="recommendations-list">
                                        {visual_analysis.visual_recommendations.map((r, i) => (
                                            <li key={i}>{r}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Visual Assessments */}
                            <div className="nb-card detailed-card assessments-card">
                                <h3 className="card-title">{t("detailed_analysis.assessments")}</h3>
                                <div className="assessments-grid">
                                    {visual_analysis.layout_assessment && (
                                        <div className="assessment-item">
                                            <h4>{t("detailed_analysis.layout_assessment")}</h4>
                                            <p>{visual_analysis.layout_assessment}</p>
                                        </div>
                                    )}
                                    {visual_analysis.typography_assessment && (
                                        <div className="assessment-item">
                                            <h4>{t("detailed_analysis.typography_assessment")}</h4>
                                            <p>{visual_analysis.typography_assessment}</p>
                                        </div>
                                    )}
                                    {visual_analysis.readability_assessment && (
                                        <div className="assessment-item">
                                            <h4>{t("detailed_analysis.readability_assessment")}</h4>
                                            <p>{visual_analysis.readability_assessment}</p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Image Quality Notes */}
                            {visual_analysis.image_quality_notes.length > 0 && (
                                <div className="nb-card detailed-card quality-notes-card">
                                    <h3 className="card-title">{t("detailed_analysis.image_quality_notes")}</h3>
                                    <ul className="quality-notes-list">
                                        {visual_analysis.image_quality_notes.map((note, i) => (
                                            <li key={i}>{note}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            </div>
                            )}
                        </section>
                    )}

                    {/* No Visual Analysis Available */}
                    {!visual_analysis && (
                        <section className="detailed-analysis-section visual-section">
                            <h2 
                                className="section-title section-title--clickable"
                                onClick={() => setIsVisualExpanded(!isVisualExpanded)}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar' || e.code === 'Space') {
                                        if (e.key === ' ' || e.key === 'Spacebar' || e.code === 'Space') {
                                            e.preventDefault();
                                        }
                                        setIsVisualExpanded(!isVisualExpanded);
                                    }
                                }}
                            >
                                <span>{t("detailed_analysis.visual_analysis")}</span>
                                <svg 
                                    className={`section-chevron ${isVisualExpanded ? 'expanded' : ''}`}
                                    viewBox="0 0 24 24" 
                                    fill="none" 
                                    stroke="currentColor" 
                                    strokeWidth="2"
                                >
                                    <path d="M6 9l6 6 6-6" />
                                </svg>
                            </h2>
                            {isVisualExpanded && (
                            <div className="section-content">
                                <div className="nb-card detailed-card no-visual-card">
                                    <p className="no-visual-message">{t("detailed_analysis.no_visual_analysis")}</p>
                                </div>
                            </div>
                            )}
                        </section>
                    )}
                </div>
            </main>
        </>
    );
};

export default DetailedAnalysis;
