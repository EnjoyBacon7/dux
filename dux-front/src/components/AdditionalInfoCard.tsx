import React, { useState } from "react";
import { useLanguage } from "../contexts/useLanguage";
import styles from "../styles/AdditionalInfoCard.module.css";

interface AdditionalInfoCardProps {
    initialValue?: string;
    onUpdate?: (context: string) => void;
}

const AdditionalInfoCard: React.FC<AdditionalInfoCardProps> = ({ initialValue = "", onUpdate }) => {
    const { t } = useLanguage();
    const [matchingContext, setMatchingContext] = useState(initialValue);
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);

    const handleContextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setMatchingContext(e.target.value);
    };

    const handleSave = async () => {
        setIsSaving(true);
        setSaveError(null);
        setSaveSuccess(false);

        try {
            const response = await fetch("/auth/profile", {
                method: "PATCH",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    matching_context: matchingContext,
                }),
            });

            if (response.ok) {
                setSaveSuccess(true);
                if (onUpdate) {
                    onUpdate(matchingContext);
                }
                // Clear success message after 3 seconds
                setTimeout(() => setSaveSuccess(false), 3000);
            } else {
                const data = await response.json();
                setSaveError(data.detail || "Failed to save additional information");
            }
        } catch {
            setSaveError("An error occurred while saving");
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className={`nb-card home-card ${styles["additional-info-card"]}`}>
            <h2 className={styles["card-title"]}>
                {t("additional_info.title")}
            </h2>
            <p className={styles["card-description"]}>
                {t("additional_info.description")}
            </p>

            <textarea
                className={styles["info-textarea"]}
                placeholder={t("additional_info.placeholder")}
                value={matchingContext}
                onChange={handleContextChange}
                disabled={isSaving}
            />

            <div className={styles["action-area"]}>
                <button
                    className={`${styles["save-button"]} ${saveSuccess ? styles["success"] : ""
                        }`}
                    onClick={handleSave}
                    disabled={isSaving || !matchingContext.trim()}
                >
                    {isSaving ? t("additional_info.saving") : t("additional_info.save")}
                </button>

                {saveSuccess && (
                    <span className={styles["success-message"]}>
                        ✓ {t("additional_info.saved")}
                    </span>
                )}

                {saveError && (
                    <span className={styles["error-message"]}>
                        ✕ {saveError}
                    </span>
                )}
            </div>
        </div>
    );
};

export default AdditionalInfoCard;
