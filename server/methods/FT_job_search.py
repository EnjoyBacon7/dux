"""
France Travail API job search integration.

Provides methods for interacting with the France Travail API to fetch
job offers using OAuth2 authentication and search parameters.
"""

import logging
import re
import requests
from typing import Dict, Any, List

from server.config import settings

logger = logging.getLogger(__name__)

# Valid parameter values for France Travail API
VALID_PARAMETERS = {
    "typeContrat": {"CDI", "CDD", "MIS", "SAI", "CCE", "FRA", "LIB", "REP", "TTI", "DDI", "DIN", "DDT"},
    "experienceExigence": {"D", "S", "E"},
    "qualification": {"0", "9"},
    # periodeSalaire expected values per France Travail: A, M, H, C
    "periodeSalaire": {"A", "M", "H", "C"},
    "dureeHebdo": {"0", "1", "2"},
    "tempsPlein": {True, False, "true", "false"},
    "publieeDepuis": {"1", "3", "7", "14", "31"},
    "sort": {"0", "1", "2"},
    # NAF division codes (secteurActivite)
    "secteurActivite": {
        "01", "02", "03", "05", "06", "07", "08", "09",
        "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
        "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
        "30", "31", "32", "33", "35", "36", "37", "38", "39",
        "41", "42", "43", "45", "46", "47", "49",
        "50", "51", "52", "53", "55", "56", "58", "59",
        "60", "61", "62", "63", "64", "65", "66", "68", "69",
        "70", "71", "72", "73", "74", "75", "77", "78", "79",
        "80", "81", "82", "84", "85", "86", "87", "88",
        "90", "91", "92", "93", "94", "95", "96", "97", "98", "99"
    },
    # Domaine codes provided by France Travail
    "domaine": {
        "A11", "A12", "A13", "A14", "A15",
        "B11", "B12", "B13", "B14", "B15", "B16", "B17", "B18",
        "C11", "C12", "C13", "C14", "C15",
        "D11", "D12", "D13", "D14", "D15",
        "E11", "E12", "E13", "E14",
        "F11", "F12", "F13", "F14", "F15", "F16", "F17",
        "G11", "G12", "G13", "G14", "G15", "G16", "G17", "G18",
        "H11", "H12", "H13", "H14", "H15",
        "H21", "H22", "H23", "H24", "H25", "H26", "H27", "H28", "H29",
        "H31", "H32", "H33", "H34",
        "I11", "I12", "I13", "I14", "I15", "I16",
        "J11", "J12", "J13", "J14", "J15",
        "K11", "K12", "K13", "K14", "K15", "K16", "K17", "K18", "K19",
        "K21", "K22", "K23", "K24", "K25", "K26",
        "L11", "L12", "L13", "L14", "L15",
        "M11", "M12", "M13", "M14", "M15", "M16", "M17", "M18",
        "N11", "N12", "N13", "N21", "N22", "N31", "N32", "N41", "N42", "N43", "N44"
    },
}


def _validate_and_clean_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean search parameters before sending to France Travail API.

    Removes invalid values and logs warnings for problematic parameters.

    Args:
        parameters: Raw parameters dict from LLM

    Returns:
        Cleaned parameters dict with invalid values removed
    """
    cleaned = {}

    # Enforce mutual exclusivity for geographic filters
    geo_keys = ["commune", "departement", "region", "paysContinent"]
    present_geo = [k for k in geo_keys if parameters.get(k) not in (None, "")]
    selected_geo = None
    if present_geo:
        # Precedence: commune > departement > region > paysContinent
        for k in ["commune", "departement", "region", "paysContinent"]:
            if parameters.get(k) not in (None, ""):
                selected_geo = k
                break
        if len(present_geo) > 1:
            logger.warning(
                "Multiple geographic filters provided %s; keeping '%s' and dropping others",
                present_geo,
                selected_geo,
            )
        # If distance is provided but selected geo is not commune, drop distance
        if selected_geo != "commune" and parameters.get("distance") not in (None, ""):
            logger.warning("Dropping 'distance' because base location is not 'commune'")
            # Remove distance by setting to empty for subsequent iteration
            parameters = {**parameters, "distance": ""}

    for key, value in parameters.items():
        if value is None or value == "":
            continue

        # Skip non-selected geographic filters
        if key in geo_keys and selected_geo and key != selected_geo:
            continue

        # Special validation for 'appellation' (expects numeric code(s))
        if key == "appellation":
            if isinstance(value, list):
                parts = [str(v).strip() for v in value if str(v).strip()]
            else:
                parts = [p.strip() for p in str(value).split(",") if p.strip()]

            filtered = [p for p in parts if re.fullmatch(r"\d+", p)]
            if not filtered:
                logger.warning("Invalid appellation value(s) '%s' (digits-only expected), removing parameter", value)
                continue
            cleaned[key] = ",".join(filtered)
            continue

        # Check if this parameter has validation rules
        if key in VALID_PARAMETERS:
            valid_values = VALID_PARAMETERS[key]
            # Booleans: normalize to lowercase strings for comparison
            if isinstance(value, bool):
                value_str = str(value).lower()
                if value_str not in valid_values:
                    logger.warning(f"Invalid {key} value '{value}' (valid: {valid_values}), removing parameter")
                    continue
                cleaned[key] = value
                continue

            # Lists or comma-separated strings: validate each entry
            if isinstance(value, list):
                parts = [str(v).strip() for v in value if str(v).strip()]
            else:
                parts = [p.strip() for p in str(value).split(",") if p.strip()]

            filtered = [p for p in parts if p in valid_values]
            if not filtered:
                logger.warning(f"Invalid {key} value(s) '{value}' (valid: {valid_values}), removing parameter")
                continue
            cleaned[key] = ",".join(filtered)
            continue

        # Remove certain problematic parameters that duplicate others
        if key == "theme" and "codeROME" in parameters:
            logger.warning("Removing 'theme' parameter (use codeROME instead)")
            continue

        cleaned[key] = value

    return cleaned


def get_ft_oauth_token(client_id: str, client_secret: str, auth_url: str) -> str:
    """
    Get OAuth2 token from France Travail authentication service.

    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        auth_url: Authentication endpoint URL

    Returns:
        OAuth2 access token

    Raises:
        Exception: If authentication fails
    """
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": f"api_offresdemploiv2 o2dsoffre application_{client_id}",
    }
    params = {"realm": "/partenaire"}

    resp = requests.post(auth_url, data=auth_data, params=params)
    resp.raise_for_status()
    return resp.json()["access_token"]


def search_france_travail(
    parameters: Dict[str, Any],
    nb_offres: int = 50,
    max_retries: int = 3
) -> List[Dict[str, Any]]:
    """
    Search for job offers from France Travail API with given parameters.

    Args:
        parameters: Dictionary of search parameters (e.g., codeROME, region, motsCles)
        nb_offres: Maximum number of offers to retrieve (default: 50)
        max_retries: Number of retries on token expiry (default: 3)

    Returns:
        List of job offer dictionaries

    Raises:
        ValueError: If search fails or API is unreachable
    """
    try:
        CLIENT_ID = settings.client_id
        CLIENT_SECRET = settings.client_secret
        AUTH_URL = settings.auth_url
        API_URL = settings.api_url_offres

        if not all([CLIENT_ID, CLIENT_SECRET, AUTH_URL, API_URL]):
            raise ValueError("France Travail API credentials not configured in environment")

        # Validate and clean parameters first
        parameters = _validate_and_clean_parameters(parameters)
        logger.debug(f"France Travail Search - Cleaned parameters: {parameters}")

        # Get OAuth2 token
        token = get_ft_oauth_token(CLIENT_ID, CLIENT_SECRET, AUTH_URL)

        # Build base headers (only auth and content-type)
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # Build query parameters (exclude None and empty string values)
        query_params = {}
        for key, value in parameters.items():
            if value is not None and value != "":
                # Convert booleans to lowercase strings as expected by API
                if isinstance(value, bool):
                    query_params[key] = str(value).lower()
                else:
                    query_params[key] = str(value)

        # Log the full request before sending
        logger.debug(f"France Travail API Request - URL: {API_URL}")
        logger.debug(f"France Travail API Request - Query params: {query_params}")

        # Fetch offers from API (handle pagination)
        offers = []
        retry_count = 0

        for i in range(0, nb_offres, 150):
            # Calculate end index, capped at nb_offres - 1 (API uses 0-based indexing)
            end_index = min(i + 149, nb_offres - 1)

            # Update range for this batch
            query_params["range"] = f"{i}-{end_index}"

            try:
                resp = requests.get(API_URL, headers=headers, params=query_params, timeout=30)
                resp.raise_for_status()

                # Handle 204 No Content (no results found)
                if resp.status_code == 204:
                    logger.info(
                        "France Travail: No results found (204 No Content) - Search params: %s",
                        query_params
                    )
                    break

                # Parse JSON response with error handling
                try:
                    data = resp.json()
                except requests.exceptions.JSONDecodeError as json_err:
                    logger.error(
                        "France Travail returned non-JSON response: status=%s headers=%s body=%s",
                        resp.status_code,
                        dict(resp.headers),
                        resp.text[:500]
                    )
                    raise ValueError(f"France Travail API returned invalid JSON: {json_err}")

                batch_results = data.get("resultats", [])
                logger.debug(f"France Travail API Response - Batch {i//150 + 1}: Received {len(batch_results)} results")
                logger.debug(f"First result sample: {batch_results[0] if batch_results else 'No results'}")
                offers.extend(batch_results)

                # If we got fewer results than requested, we've reached the end
                if len(data.get("resultats", [])) < 150:
                    break

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401 and retry_count < max_retries:
                    # Token expired, refresh and retry
                    logger.warning(f"Token expired, refreshing (attempt {retry_count + 1}/{max_retries})")
                    token = get_ft_oauth_token(CLIENT_ID, CLIENT_SECRET, AUTH_URL)
                    headers["Authorization"] = f"Bearer {token}"
                    retry_count += 1

                    # Retry the request with updated token
                    resp = requests.get(API_URL, headers=headers, params=query_params, timeout=30)
                    resp.raise_for_status()

                    # Handle 204 No Content on retry
                    if resp.status_code == 204:
                        logger.info(
                            "France Travail: No results found on retry (204 No Content) - Search params: %s",
                            query_params
                        )
                        break

                    try:
                        data = resp.json()
                    except requests.exceptions.JSONDecodeError as json_err:
                        logger.error(
                            "France Travail returned non-JSON response on retry: status=%s body=%s",
                            resp.status_code,
                            resp.text[:500]
                        )
                        raise ValueError(f"France Travail API returned invalid JSON on retry: {json_err}")

                    batch_results = data.get("resultats", [])
                    logger.debug(f"France Travail API Response (retry) - Batch {i//150 + 1}: Received {len(batch_results)} results")
                    offers.extend(batch_results)
                else:
                    # Log detailed France Travail error payload if available
                    status = getattr(e.response, "status_code", "Unknown")
                    err_text = None
                    err_json = None
                    try:
                        err_json = e.response.json()
                    except Exception:
                        try:
                            err_text = e.response.text
                        except Exception:
                            err_text = str(e)

                    if isinstance(err_json, dict):
                        logger.error(
                            "France Travail API error: status=%s codeErreur=%s message=%s",
                            status,
                            err_json.get("codeErreur"),
                            err_json.get("message")
                        )
                    else:
                        logger.error("France Travail API error: status=%s body=%s", status, err_text)
                    raise

        logger.info(f"France Travail: Successfully retrieved {len(offers)} total offers from parameters: {parameters}")
        return offers

    except requests.exceptions.RequestException as e:
        logger.error(f"France Travail API request error: {str(e)}")
        raise ValueError(f"Failed to communicate with France Travail API: {str(e)}")
    except Exception as e:
        logger.error(f"France Travail search error: {str(e)}")
        raise ValueError(f"France Travail job search failed: {str(e)}")
