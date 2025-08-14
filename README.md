# Resonance Agent

Bu, istifadəçilərlə dərin, kontekstli və empatik dialoqlar qurmaq üçün nəzərdə tutulmuş ağıllı bir AI agentinin prototipidir.

## Xüsusiyyətləri

- **Modulyar Arxitektura:** Agentin "beynini" (NLP Mühərriki, Cavab Generatoru) asanlıqla dəyişmək mümkündür.
- **İkili Mühərrik Dəstəyi:** Həm güclü bulud API-ləri (Google Gemini), həm də şəxsi kompüterdə işləyən lokal modellərlə (Ollama vasitəsilə) işləyə bilir.
- **Kontekstli Yaddaş:** Agent, söhbətləri xatırlamaq və gələcək interaksiyalarda istifadə etmək üçün vektor verilənlər bazasından (ChromaDB) istifadə edir.
- **Dərin Niyyət Analizi:** İstifadəçinin mesajını təkcə mətn olaraq deyil, həm də emosiya, təcililik və mürəkkəblik kimi bir çox parametr üzrə analiz edir.

## Qurulum və İşə Salma

1.  **Layihəni Klonlayın (əgər `git` istifadə edirsinizsə) və ya qovluğa daxil olun.**

2.  **Terminalı (Command Prompt/PowerShell) açın və layihə qovluğuna keçin:**
    ```bash
    cd C:\Users\mahir\ResonanceAgent
    ```

3.  **Virtual Mühit Yaradın və Aktivləşdirin:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

4.  **Lazımi Kitabxanaları Quraşdırın:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Konfiqurasiya Faylını Hazırlayın:**
    - `.env.example` faylının adını `.env` olaraq dəyişin.
    - `.env` faylını bir mətn redaktoru ilə açın və içindəki təlimatlara uyğun olaraq doldurun. `ENGINE_TYPE` seçiminizə görə ya `GOOGLE_API_KEY`, ya da lokal model parametrlərini təyin edin.

6.  **Agenti İşə Salın:**
    ```bash
    python main.py
    ```

Artıq agentlə terminalda dialoqa başlaya bilərsiniz. Çıxmaq üçün `exit` və ya `quit` yazın.
