import React from "react";
import { useLanguage } from "../contexts/useLanguage";

interface OfferBoxProps {
    title: string;
    company?: string;
    location?: string;
    contractType?: string;
    date?: string | null;
    description?: string;
    salary?: string;
    onViewDetails?: () => void;
    showViewButton?: boolean;
    onClick?: () => void;
    className?: string;
}

const OfferBox: React.FC<OfferBoxProps> = ({
    title,
    company,
    location,
    contractType,
    date,
    description,
    salary,
    onViewDetails,
    showViewButton = true,
    onClick,
    className,
}) => {
    const { t } = useLanguage();

    const formatDate = (dateString: string | null | undefined) => {
        if (!dateString) return undefined;
        try {
            const dateObj = new Date(dateString);
            const now = new Date();
            const diffTime = Math.abs(now.getTime() - dateObj.getTime());
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays === 1) return t('jobs.posted_today');
            if (diffDays < 7) return t('jobs.posted_days_ago').replace('{days}', diffDays.toString());
            if (diffDays < 30) {
                const weeks = Math.floor(diffDays / 7);
                return t('jobs.posted_weeks_ago').replace('{weeks}', weeks.toString());
            }
            return dateObj.toLocaleDateString();
        } catch {
            return dateString || undefined;
        }
    };

    return (
        <div
            className={className}
            onClick={onClick}
            style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', cursor: onClick ? 'pointer' : 'default' }}
        >
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                    <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.25rem' }}>{title}</h3>
                    <p style={{ margin: 0, fontSize: '1rem', opacity: 0.8 }}>
                        {company || t('jobs.company_not_specified')}
                    </p>
                </div>
                {salary && (
                    <div style={{ fontWeight: 600, color: 'var(--nb-accent)', textAlign: 'right', fontSize: '1rem' }}>
                        {salary}
                    </div>
                )}
            </div>

            {/* Meta */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', fontSize: '0.875rem', opacity: 0.7 }}>
                {location && (
                    <>
                        <span>📍 {location}</span>
                        <span>•</span>
                    </>
                )}
                {contractType && (
                    <>
                        <span>💼 {contractType}</span>
                        <span>•</span>
                    </>
                )}
                {formatDate(date) && <span>📅 {formatDate(date)}</span>}
            </div>

            {/* Description */}
            {description && (
                <p style={{ margin: 0, lineHeight: 1.6 }}>
                    {description.length > 200 ? description.substring(0, 200) + '...' : description}
                </p>
            )}

            {/* Actions */}
            {showViewButton && (
                <div style={{ marginTop: '0.5rem' }}>
                    <button onClick={onViewDetails} className="nb-btn">
                        {t('jobs.view_details')}
                    </button>
                </div>
            )}
        </div>
    );
};

export default OfferBox;
