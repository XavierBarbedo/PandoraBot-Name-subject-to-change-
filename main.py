from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import google.generativeai as genai
import re
import time

# ─────────────────────────────────────────
# CONFIGURAÇÃO DO GOOGLE GEN AI / GEMINI
# ─────────────────────────────────────────
genai.configure(api_key="AIzaSyDiQFZuZCcyd7SGPlWSPmGLO3Hjj6u7FEA")
model = genai.GenerativeModel("gemini-2.5-flash")

# ─────────────────────────────────────────
# FUNÇÃO PARA CHAMAR GEMINI
# ─────────────────────────────────────────
def gerar_resposta_gemini(prompt, max_tokens=1000):
    """Chama o modelo Gemini e retorna o texto da resposta."""
    try:
        resp = model.generate_content(
            [prompt],
            generation_config={
                "temperature": 0,
                "max_output_tokens": max_tokens
            }
        )
        print(resp)

        # Verifica se há candidatos e partes
        if resp and hasattr(resp, "candidates") and resp.candidates:
            cand = resp.candidates[0]
            if hasattr(cand, "content") and cand.content.parts:
                part = cand.content.parts[0]
                if hasattr(part, "text"):
                    return part.text.strip()

        return ""  # Retorna vazio se não encontrou texto
    except Exception as e:
        print("Erro API Gemini:", e)
        return ""


# ─────────────────────────────────────────
# FUNÇÃO PARA INTERPRETAR RESPOSTA
# ─────────────────────────────────────────
def interpretar_resposta(resposta, num_opcoes):
    """
    Interpreta a resposta do modelo Gemini.
    - Remove caracteres não numéricos
    - Procura todos os números
    - Retorna o primeiro número válido dentro do intervalo de opções
    """
    # Remove tudo que não seja dígito ou espaço
    clean = re.sub(r"[^\d\s]", " ", resposta)
    numeros = re.findall(r"\d+", clean)
    
    for n in numeros:
        num = int(n)
        if 1 <= num <= num_opcoes:
            return num
    return None

# ─────────────────────────────────────────
# INICIALIZA SELENIUM
# ─────────────────────────────────────────
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://b.socrative.com/login/student/")
wait = WebDriverWait(driver, 90)

# ─────────────────────────────────────────
# LOOP PRINCIPAL
# ─────────────────────────────────────────
while True:
    try:
        # Captura pergunta
        question_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "question-text")))
        question_text = question_element.text
        print("\nPergunta:", question_text)

        # Captura alternativas
        answers_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "mc-answer-option-text")))
        answers = [a.text for a in answers_elements]

        print(f"Foram encontradas {len(answers)} respostas:")
        for i, ans in enumerate(answers, start=1):
            print(f"{i}) {ans}")

        # Monta prompt reforçado para Gemini
        prompt = f"""
Você é um modelo que analisa perguntas de múltipla escolha.
Responda APENAS com o número da opção correta, nada mais, sem explicações.

Pergunta: {question_text}

Opções:
{chr(10).join(f"{i+1}) {ans}" for i, ans in enumerate(answers))}

Responda SOMENTE com o número da opção correta (1-{len(answers)}).
"""
        # Chama Gemini
        resposta_texto = gerar_resposta_gemini(prompt, max_tokens=1000)

        print("\nResposta bruta do Gemini:", resposta_texto)

        # Interpreta a resposta
        escolha = interpretar_resposta(resposta_texto, len(answers))
        if escolha:
            resposta_final = answers[escolha-1]
        else:
            resposta_final = "Erro: não consegui interpretar a resposta."

        print(f"\nNúmero sugerido: {escolha}")
        print(f"Resposta sugerida: {resposta_final}")

        input("\nPressione ENTER para a próxima pergunta…")

    except Exception as e:
        print("Erro geral:", e)
        print("Tentando novamente em 5 segundos...")
        time.sleep(5)
        continue

driver.quit()
