# Profile Setup Feature

## Overview

The profile setup feature provides a guided onboarding experience for new users after registration. It collects comprehensive professional information including CV uploads, work experience, education, and skills.

## User Flow

1. **Registration**: User creates an account via password or passkey
2. **Automatic Redirect**: After successful registration, user is automatically redirected to `/setup`
3. **Multi-Step Setup**:
   - **Step 1: CV Upload** - Upload resume/CV (PDF, DOC, DOCX)
   - **Step 2: Profile Info** - Add headline, location, summary, and skills
   - **Step 3: Work Experience** - Add professional experience entries
   - **Step 4: Education** - Add educational background
4. **Completion**: Profile is saved and user is redirected to home page

## Features

### CV Upload
- Accepts PDF, DOC, and DOCX formats
- Stores file in `uploads/` directory
- Filename saved in user's `cv_filename` field
- Can be skipped for later completion

### Profile Information
- **Professional Headline**: Job title or professional identity
- **Location**: City, state, or country
- **Professional Summary**: Free-text description of background and goals
- **Skills**: Tag-based skill list with add/remove functionality

### Work Experience
- Multiple entries supported
- Fields: Company, Title, Start Date, End Date, Description
- "Currently work here" checkbox (nullifies end date)
- Remove individual entries

### Education
- Multiple entries supported
- Fields: School, Degree, Field of Study, Start Date, End Date, Description
- Remove individual entries

### Skip Option
- Users can skip setup entirely and complete later
- Skipping does NOT mark profile as completed
- Can re-enter setup by navigating to `/setup`

## Technical Implementation

### Frontend

**Component**: `ProfileSetup.tsx`
- Multi-step wizard with progress indicator
- Form validation
- API integration for data submission
- Responsive design with neo-brutalism styling

**Routing**: Integrated in `App.tsx`
```tsx
<Route path="/setup" element={<RequireAuth><ProfileSetup /></RequireAuth>} />
```

**Auth Guard**: `RequireAuth.tsx`
- Checks `user.profile_setup_completed` flag
- Redirects incomplete profiles to `/setup`
- Allows setup page access even when incomplete

### Backend

**Models** (`server/models.py`):
```python
class User:
    # Profile fields
    email = Column(String, nullable=True)
    headline = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    linkedin_profile_url = Column(String, nullable=True)
    cv_filename = Column(String, nullable=True)
    skills = Column(ARRAY(String), nullable=True)
    profile_setup_completed = Column(Boolean, default=False)
    
    # Relationships
    experiences = relationship("Experience", ...)
    educations = relationship("Education", ...)

class Experience:
    user_id, company, title, start_date, end_date, 
    is_current, description

class Education:
    user_id, school, degree, field_of_study, 
    start_date, end_date, description
```

**API Endpoints** (`server/api.py`):

1. **POST /api/upload**
   - Uploads CV file
   - Updates `user.cv_filename`
   - Requires authentication

2. **POST /api/profile/setup**
   - Accepts ProfileSetupRequest payload
   - Updates user profile fields
   - Creates/replaces experience and education entries
   - Sets `profile_setup_completed = True`
   - Requires authentication

**Request Models**:
```python
class ExperienceData(BaseModel):
    company: str
    title: str
    startDate: str
    endDate: Optional[str] = None
    isCurrent: bool = False
    description: Optional[str] = None

class EducationData(BaseModel):
    school: str
    degree: str
    fieldOfStudy: Optional[str] = None
    startDate: str
    endDate: Optional[str] = None
    description: Optional[str] = None

class ProfileSetupRequest(BaseModel):
    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = []
    experiences: List[ExperienceData] = []
    educations: List[EducationData] = []
```

### Database Migration

**Script**: `server/migrations/add_profile_setup_fields.py`

Adds:
- User profile columns (email, headline, summary, location, industry, linkedin_profile_url, cv_filename, skills, profile_setup_completed)
- `experiences` table
- `educations` table
- Indexes on user_id for performance

**Run migration**:
```bash
python -m server.migrations.add_profile_setup_fields
```

## Translations

All UI text is fully internationalized with support for:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Portuguese (pt)
- Latin (la)

Translation keys in `LanguageContext.tsx`:
- `setup.title`, `setup.description`
- `setup.cv_upload`, `setup.upload_cv`, `setup.skip_cv`
- `setup.profile_info`, `setup.headline`, `setup.location`, `setup.summary`, `setup.skills`
- `setup.experience`, `setup.company`, `setup.job_title`, `setup.start_date`, `setup.end_date`
- `setup.education`, `setup.school`, `setup.degree`, `setup.field_of_study`
- And more...

## Security

- All endpoints require authentication (session-based)
- User can only modify their own profile
- File uploads validated by type
- Rate limiting applied to registration endpoints

## Future Enhancements

- [ ] Edit profile after initial setup
- [ ] Profile completeness indicator
- [ ] Rich text editor for summaries
- [ ] Resume parsing to auto-fill fields
- [ ] LinkedIn profile import
- [ ] Profile preview before submission
- [ ] Save progress between steps
- [ ] Profile visibility settings
