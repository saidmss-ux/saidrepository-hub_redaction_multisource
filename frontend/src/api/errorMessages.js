export const ERROR_MESSAGES = {
  validation_error: "Certaines informations saisies sont invalides.",
  internal_error: "Une erreur interne est survenue.",
  over_capacity: "Le service est momentanément surchargé. Veuillez réessayer.",
  upload_too_large: "Le document dépasse la taille maximale autorisée.",
  unsupported_file_type: "Ce type de fichier n'est pas pris en charge.",
  invalid_url_scheme: "Seules les URL http/https sont autorisées.",
  invalid_url: "L'URL fournie est invalide.",
  blocked_host: "Cette adresse n'est pas autorisée.",
  blocked_private_network: "Les réseaux privés ne sont pas autorisés.",
  dns_resolution_failed: "Impossible de résoudre le domaine demandé.",
  network_http_error: "Erreur HTTP pendant le téléchargement.",
  network_url_error: "Erreur réseau pendant le téléchargement.",
  network_timeout: "Le délai réseau a été dépassé.",
  file_not_found: "La source demandée est introuvable.",
  extract_timeout: "Le délai d'extraction a été dépassé.",
  api_key_disabled: "La clé API IA est désactivée.",
  unknown_error: "Une erreur inconnue est survenue.",
};

export function messageForCode(code) {
  if (!code) {
    return ERROR_MESSAGES.unknown_error;
  }
  return ERROR_MESSAGES[code] || ERROR_MESSAGES.unknown_error;
}
