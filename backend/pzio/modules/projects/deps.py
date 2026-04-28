from uuid import UUID
from fastapi import Header, HTTPException

def get_current_user_mock(authorization: str = Header(None)) -> UUID:
    """
    Tymczasowa zaślepka (mock) dla autoryzacji.
    Gdy Moduł 1 będzie gotowy, podmienimy to na ich prawdziwą funkcję.
    """
    if not authorization:
        # Zgodnie z SAD, API zawsze zwraca błędy w formacie {"detail": "Opis błędu"} [cite: 90, 101]
        raise HTTPException(status_code=401, detail="Brak tokenu autoryzacji")
    
    # Zwracamy sztuczne, losowe ID użytkownika, żeby móc testować dodawanie projektów
    return UUID("12345678-1234-5678-1234-567812345678")