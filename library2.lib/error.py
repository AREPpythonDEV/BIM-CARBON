#! python3
# -*- coding: utf-8 -*-
import sys
from enum import Enum
import traceback
from textwrap import dedent
from debug import debug_print
from help_links import HelpLinks


class ErrorCode(Enum):
    """Enumeration of all possible error codes with their default messages and dialog info"""

    def __init__(self, code, message, dialog_title=None, dialog_details=None, help_link=None, help_text=None):
        self.code = code
        self.message = message
        self.dialog_title = dialog_title or "Erreur"
        self.dialog_details = dialog_details or ""

        if isinstance(help_link, Enum):
            self.help_link = help_link.value
        else:
            self.help_link = help_link or ""
        self.help_text = help_text or ""

    # Worksharing specific errors
    NOT_WORKSHARED = (
        'NOT_WORKSHARED',
        'La maquette n\'est pas partagée. Le calcul carbone se base sur les sous-projets pour identifier les lots.',
        'Calculer le projet - Calcul abandonné',
        'Veuillez partager la maquette et relancer le calcul.\nLes sous-projets acceptés doivent commencer par 2_, 3_ ou 4_ pour être reconnus.',
        '',
        ''
    )
    NO_VALID_WORKSETS = (
        'NO_VALID_WORKSETS',
        'La maquette est partagée mais aucun sous-projet AREP valide n\'a été trouvé. Merci de vérifier la présence de ces sous-projets et relancer le calcul.',
        'Calculer le projet - Calcul abandonné',
        'Dans la version actuelle, les sous-projets acceptés doivent commencer par 2_, 3_ ou 4_ pour être reconnus.',
        '',
        ''
    )
    WORKSET_ACCESS_ERROR = (
        'WORKSET_ACCESS_ERROR',
        'Une erreur s\'est produite lors de l\'accès aux sous-projets.',
        'Erreur d\'accès aux sous-projets',
        '',
        '',
        ''
    )

    # Selection errors
    NO_USER_SELECTION = (
        'NO_USER_SELECTION',
        'Aucun élément n\'a été sélectionné pour le calcul. L\'opération a été annulée.',
        'Calculer le projet',
        '',
        '',
        ''
    )
    NO_ELEMENTS_SELECTED = (
        'NO_ELEMENTS_SELECTED',
        'Aucun élément sélectionné.',
        'Calculer le projet - Erreur',
        'Le calcul est abandonné.',
        '',
        ''
    )
    SELECTION_CANCELLED = (
        'SELECTION_CANCELLED',
        'Sélection annulée par l\'utilisateur.',
        'Calculer le projet',
        '',
        '',
        ''
    )

    # Processing errors
    NO_COMPRESSED_DICO = (
        'NO_COMPRESSED_DICO',
        'Les éléments de la maquette n\'ont pas pu être extraits.',
        'Calcul abandonné',
        'No compressed_dico',
        '',
        ''
    )
    NO_FILTERED_ELEMENTS = (
        'NO_FILTERED_ELEMENTS',
        'Aucun élément filtré trouvé.',
        'Calcul abandonné',
        '',
        '',
        ''
    )
    MATERIAL_EXTRACTION_FAILED = (
        'MATERIAL_EXTRACTION_FAILED',
        'Échec de l\'extraction des matériaux.',
        'Erreur de traitement',
        '',
        '',
        ''
    )
    ELEMENT_PROCESSING_ERROR = (
        'ELEMENT_PROCESSING_ERROR',
        'Erreur lors du traitement d\'un élément.',
        'Erreur de traitement',
        '',
        '',
        ''
    )
    NO_MATERIAL_VOLUMES_FOUND = (
        'NO_MATERIAL_VOLUME_FOUND',
        'Aucun volume de matériau n\'a été trouvé pour les éléments sélectionnés.',
        'Erreur de traitement',
        dedent(
            """
            Cette erreur peut se produire lorsque les éléments sélectionnés n'ont
            pas de matériaux assignés ou que la catégorie ne permet pas le calcul des volumes dans Revit.
            Vous pouvez essayer de modifier la sélection des éléments
            et relancer le calcul.
            """
        ),
        '',
        ''
    )
    NO_KNOWN_MATERIALS_FOUND = (
        'NO_KNOWN_MATERIALS_FOUND',
        'Aucun matériau reconnu n\'a été trouvé parmi les éléments calculés.',
        'Erreur de traitement',
        dedent(
            """
            Cette erreur peut se produire lorsque les matériaux des éléments
            sélectionnés ne figurent pas dans la base de données des matériaux connus.
            Veuillez vérifier les matériaux assignés aux éléments ainsi que leurs classes et relancez le calcul.
            """
        ),
        HelpLinks.MATERIALS,
        'Quelles sont les classes de matériaux autorisées ?'
    )

    # Generic errors
    PARAMETER_ACCESS_ERROR = (
        'PARAMETER_ACCESS_ERROR',
        'Erreur d\'accès aux paramètres.',
        'Erreur',
        '',
        '',
        ''
    )
    DOCUMENT_ACCESS_ERROR = (
        'DOCUMENT_ACCESS_ERROR',
        'Erreur d\'accès au document.',
        'Erreur',
        '',
        '',
        ''
    )
    SHARED_PARAMETER_FILE_NOT_SET = (
        'SHARED_PARAMETER_FILE_NOT_SET',
        'Le fichier de paramètres partagés n\'est pas configuré ou le groupe "EMC2B" est introuvable.',
        'Configuration requise - Paramètres partagés',
        'Veuillez configurer le fichier de paramètres partagés :\n\n'
        '1. Allez dans Gérer > Paramètres partagés\n'
        '2. Pointez vers le bon fichier de paramètres partagés\n'
        '3. Vérifiez que le groupe "EMC2B" existe\n'
        '4. Relancez la commande',
        '',
        ''
    )
    CATEGORY_NOT_FOUND = (
        'CATEGORY_NOT_FOUND',
        'La catégorie requise n\'a pas été trouvée dans le document.',
        'Erreur de catégorie',
        '',
        '',
        ''
    )
    TRANSACTION_FAILED = (
        'TRANSACTION_FAILED',
        'La transaction a échoué.',
        'Erreur de transaction',
        '',
        '',
        ''
    )
    UNKNOWN_ERROR = (
        'UNKNOWN_ERROR',
        'Une erreur inconnue s\'est produite.',
        'Erreur',
        '',
        '',
        ''
    )


class CustomError(Exception):
    """Custom exception class for pyRevit extension with UI message mapping"""

    def __init__(self, error_code, message=None, details=None):
        if isinstance(error_code, ErrorCode):
            self.error_code = error_code
            self.message = message or error_code.message
        else:
            try:
                self.error_code = next(e for e in ErrorCode if e.code == error_code)
                self.message = message or self.error_code.message
            except StopIteration:
                self.error_code = ErrorCode.UNKNOWN_ERROR
                self.message = message or ErrorCode.UNKNOWN_ERROR.message

        self.details = details
        super().__init__(self.message)

    def get_ui_message(self):
        """Get the formatted message for UI display"""
        if self.details:
            return f"{self.message}\n\nDétails: {self.details}"
        return self.message

    def get_error_code(self):
        """Get the error code value for logging or debugging"""
        return self.error_code.code

    def get_dialog_title(self):
        """Get the dialog title for this error"""
        return self.error_code.dialog_title

    def get_dialog_message(self):
        """Get the dialog message for this error"""
        return self.message

    def get_dialog_details(self):
        """Get the dialog details for this error"""
        if self.details:
            return self.details
        return self.error_code.dialog_details

    def get_help_link(self):
        """Get the dialog help link for this error if available"""
        return self.error_code.help_link

    def get_help_text(self):
        """Get the dialog help text for this error if available"""
        return self.error_code.help_text

    @classmethod
    def from_dict(cls, error_dict):
        """Create exception from dictionary"""
        error_code = error_dict['error_code']

        if isinstance(error_code, str):
            try:
                error_code = next(e for e in ErrorCode if e.code == error_code)
            except StopIteration:
                error_code = ErrorCode.UNKNOWN_ERROR

        return cls(
            error_code,
            error_dict.get('message'),
            error_dict.get('details')
        )

    def to_dict(self):
        """Convert exception to dictionary"""
        return {
            'error_code': self.error_code.code,
            'message': self.message,
            'details': self.details
        }


class OperationResult:
    """Wrapper class for operation results that can contain errors or success data"""

    def __init__(self, success=True, data=None, error=None):
        self.success = success
        self.data = data
        self.error = error
        self.error_stack = []
        self.traceback = ''

    @classmethod
    def success_result(cls, data=None):
        """Create a successful result"""
        return cls(success=True, data=data)

    @classmethod
    def error_result(cls, error_code, message=None, details=None, context=None):
        """Create an error result using ErrorCode enum"""
        if isinstance(error_code, ErrorCode):
            code_value = error_code.code
        else:
            code_value = error_code

        error_dict = {
            'error_code': code_value,
            'message': message,
            'details': details
        }

        result = cls(success=False, error=error_dict)
        if context:
            result.error_stack.append(context)

        exc_info = sys.exc_info()
        if exc_info[0] is not None:
            result.traceback = ''.join(traceback.format_exception(*exc_info))

        return result

    @classmethod
    def from_exception(cls, exception):
        """Create error result from CustomError or generic exception"""
        if isinstance(exception, CustomError):
            return cls(success=False, error=exception.to_dict())
        else:
            return cls.error_result(
                ErrorCode.UNKNOWN_ERROR,
                'Une erreur inattendue s\'est produite',
                str(exception)
            )

    def add_context(self, context):
        """Add context information when propagating error up"""
        if not self.success:
            self.error_stack.append(context)
        return self

    def get_full_context(self):
        """Get full error context for debugging"""
        if self.success:
            return None

        context_chain = " > ".join(reversed(self.error_stack))
        return f"Error path: {context_chain}" if context_chain else None

    def show_error_dialog(self, show_dialog_func=None):
        """
        Show error dialog if this result contains an error

        Returns:
            bool: True if error was shown, False if no error
        """
        if not self.success and self.error:
            error = CustomError.from_dict(self.error)

            # Build expanded content with error code, context, and traceback
            expanded_parts = []

            # Add error code
            expanded_parts.append(f"Error Code: {error.get_error_code()}")

            # Add context chain if exists
            context_chain = self.get_full_context()
            if context_chain:
                expanded_parts.append(context_chain)

            # Add traceback if this is an unexpected error
            if hasattr(self, 'traceback') and self.traceback:
                expanded_parts.append(f"{self.traceback}")

            expanded_content = "\n\n".join(expanded_parts) if expanded_parts else None

            if show_dialog_func is None:
                from forms import show_taskdialog
                show_dialog_func = show_taskdialog

            show_dialog_func(
                error.get_dialog_title(),
                error.get_dialog_message(),
                error.get_dialog_details(),
                expanded_content=expanded_content,
                footer_text=error.get_help_link(),
                help_replacement=error.get_help_text()
            )

            # Debug logging
            debug_print(f"Error [{error.get_error_code()}]: {error.message}")
            if error.details:
                debug_print(f"Details: {error.details}")
            if context_chain:
                debug_print(f"Context: {context_chain}")
            if hasattr(self, 'traceback') and self.traceback:
                debug_print(f"Traceback:\n{self.traceback}")

            return True
        return False

    def raise_if_error(self):
        """Raise the exception if this result contains an error"""
        if not self.success and self.error:
            raise CustomError.from_dict(self.error)
