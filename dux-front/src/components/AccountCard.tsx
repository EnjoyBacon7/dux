import React from "react";

interface AccountCardProps {
    username: string;
    firstName?: string;
    lastName?: string;
    title?: string;
    profilePicture?: string;
}

const AccountCard: React.FC<AccountCardProps> = ({ 
    username, 
    firstName, 
    lastName, 
    title,
    profilePicture 
}) => {
    // Generate initials from first and last name, or username
    const getInitials = () => {
        if (firstName && lastName) {
            return `${firstName[0]}${lastName[0]}`.toUpperCase();
        }
        if (firstName) {
            return firstName[0].toUpperCase();
        }
        return username.substring(0, 2).toUpperCase();
    };

    return (
        <div className="nb-card">
            <h2 style={{ margin: '0 0 1rem 0' }}>Account</h2>
            <div className="nb-account-card-content">
                <div className="nb-account-avatar">
                    {profilePicture ? (
                        <img src={profilePicture} alt={`${username}'s profile`} />
                    ) : (
                        <div className="nb-account-avatar-placeholder">
                            {getInitials()}
                        </div>
                    )}
                </div>
                <div className="nb-account-details">
                    <div className="nb-account-name">
                        {firstName || lastName ? (
                            <>
                                {firstName && <span className="nb-account-first-name">{firstName}</span>}
                                {lastName && <span className="nb-account-last-name">{lastName}</span>}
                            </>
                        ) : (
                            <span className="nb-account-username">{username}</span>
                        )}
                    </div>
                    {title && (
                        <div className="nb-account-title">{title}</div>
                    )}
                    <div className="nb-account-username-small">@{username}</div>
                </div>
            </div>
        </div>
    );
};

export default AccountCard;
