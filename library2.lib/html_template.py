# -*- coding: utf-8 -*-
"""
Template HTML et fonctions de génération pour le rapport carbone AREP.
"""
import os


def get_css_content(css_file_path):
    """
    Lit le contenu du fichier CSS et le retourne comme string.
    Si le fichier n'existe pas, retourne un CSS par défaut minimal.
    """
    if os.path.exists(css_file_path):
        with open(css_file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        # CSS de secours minimal si le fichier n'est pas trouvé
        return """
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: #f5f5f5; 
        }
        .container { max-width: 1200px; margin: 0 auto; }
        """


def generate_html_header(css_content, title="Rapport Carbone AREP"):
    """Génère le header HTML avec le CSS injecté."""
    return f"""<!DOCTYPE html>
<html lang='fr'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>{title}</title>
    <link href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap' rel='stylesheet'>
    <style>
{css_content}
    </style>
</head>
<body>
"""


def generate_page_header(project_name):
    """Génère le header visuel de la page."""
    return f"""    <div class='header'>
        <div class='container'>
            <div class='header-content'>
                <div class='header-main'>
                    <div class='header-title'>
                        <h1>Impact Carbone</h1>
                        <div class='header-subtitle'>Projet: {project_name}</div>
                        <div class='header-meta'>Analyse environnementale complète</div>
                    </div>
                    <div class='header-logo'>
                        <div class='logo-arep'>AREP</div>
                        <div class='logo-bim'>BIM</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
"""


def generate_stats_cards(total_weight, total_elements, format_number):
    """Génère les cartes de statistiques."""
    return f"""    <div class='container'>
        <div class='stats-grid'>
            <div class='stat-card'>
                <div class='stat-number'>{format_number(total_weight)}</div>
                <div class='stat-label'>kgCO₂e - Résultats poids carbone</div>
            </div>
            <div class='stat-card'>
                <div class='stat-number'>{format_number(total_elements)}</div>
                <div class='stat-label'>Éléments calculés</div>
            </div>
        </div>
"""


def generate_intro_section():
    """Génère la section d'introduction."""
    return """        <div class='intro'>
            <p>L'outil calcule une estimation globale du bilan carbone en utilisant les données disponibles dans le modèle. Il permet ainsi aux décideurs de comprendre rapidement l'impact environnemental potentiel de la construction.</p>
            <p><strong>Prérequis :</strong></p>
            <ul style='margin-left: 20px; margin-top: 10px;'>
                <li>Les matériaux d'un objet doivent être définis selon le référentiel intégré dans le gabarit AREP</li>
                <li>Les éléments doivent respecter la charte de modélisation AREP</li>
                <li>Les éléments doivent être classés dans le bon sous-projet AREP</li>
            </ul>
            <p style='margin-top: 15px;'><em>Note : À ce jour, l'outil calcule uniquement les éléments de la structure, clos couvert et du second œuvre.</em></p>
        </div>
"""


def generate_table_section(title, headers, data_rows, format_number, highlight_threshold=10):
    """
    Génère une section avec un tableau.

    Args:
        title: Titre de la section
        headers: Liste des en-têtes de colonnes
        data_rows: Liste de tuples contenant les données
        format_number: Fonction pour formater les nombres
        highlight_threshold: Seuil de pourcentage pour le highlight
    """
    html = f"""        <div class='section'>
            <h3 class='section-title'>{title}</h3>
            <div class='table-container'>
                <table>
                    <thead>
                        <tr>
"""

    # Headers
    for header in headers:
        html += f"                            <th>{header}</th>\n"

    html += """                        </tr>
                    </thead>
                    <tbody>
"""

    # Data rows
    for row in data_rows:
        html += "                        <tr>\n"
        for i, cell in enumerate(row):
            if i == 0:  # Première colonne en gras
                html += f"                            <td><strong>{cell}</strong></td>\n"
            elif i == 1 and isinstance(cell, (int, float)):  # Colonne pourcentage
                highlight_class = " class='highlight'" if cell > highlight_threshold else ""
                html += f"                            <td><span{highlight_class}>{cell:.2f}%</span></td>\n"
            elif isinstance(cell, (int, float)):  # Autres nombres
                html += f"                            <td>{format_number(cell)}</td>\n"
            else:  # Texte normal
                html += f"                            <td>{cell}</td>\n"
        html += "                        </tr>\n"

    html += """                    </tbody>
                </table>
            </div>
        </div>
"""
    return html


def generate_chart_section(title, chart_html, large=False):
    """
    Génère une section avec un graphique Plotly.

    Args:
        title: Titre de la section
        chart_html: HTML du graphique Plotly
        large: Si True, utilise le container large (pour camembert)
    """
    container_class = "chart-container-large" if large else "chart-container"

    return f"""        <div class='section'>
            <h3 class='section-title'>{title}</h3>
            <div class='{container_class}'>
{chart_html}
            </div>
        </div>
"""


def generate_scroll_buttons_and_scripts():
    """Génère les boutons de scroll et les scripts JavaScript."""
    return """    </div>

    <button id='scrollTopBtn' class='scroll-btn' onclick='scrollToTop()'>↑</button>
    <button id='scrollBottomBtn' class='scroll-btn' onclick='scrollToBottom()'>↓</button>

    <script>
        function scrollToTop() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function scrollToBottom() {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        }

        // Animation au scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animation = 'fadeInUp 0.6s ease-out';
                }
            });
        }, observerOptions);

        document.addEventListener('DOMContentLoaded', function() {
            const sections = document.querySelectorAll('.section');
            sections.forEach(section => {
                observer.observe(section);
            });
        });
    </script>
</body>
</html>
"""
