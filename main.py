from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import google.generativeai as genai
import re
import time
import os
import sys
import keyboard  # <<< PARA DETECTAR A TECLA

def resource_path(relative_path):
    """Retorna o caminho correto para arquivos tanto no Python quanto no EXE."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


import os
import sys

def carregar_api_key():
    try:
        # Pega a pasta do EXE ou do script Python
        pasta_atual = os.path.dirname(sys.executable)
        file_path = os.path.join(pasta_atual, "apikey.txt")

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    except Exception as e:
        print("❌ ERRO: Não foi possível ler o ficheiro 'apikey.txt'")
        print("Erro:", e)
        sys.exit(1)


API_KEY = carregar_api_key()
print("API Key carregada com sucesso:", API_KEY)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


paused = False

def toggle_pause(event):
    global paused
    paused = not paused
    print("\n⏸ PAUSADO" if paused else "\n▶ CONTINUANDO...")


keyboard.on_press_key("num lock", toggle_pause)


def esperar_pausa():
    """Fica preso aqui enquanto a pausa estiver ativa."""
    while paused:
        time.sleep(0.2)


def gerar_resposta_gemini(prompt, max_tokens=1000):
    try:
        resp = model.generate_content(
            [prompt],
            generation_config={
                "temperature": 0,
                "max_output_tokens": max_tokens
            }
        )

        if resp and hasattr(resp, "candidates") and resp.candidates:
            cand = resp.candidates[0]
            if hasattr(cand, "content") and cand.content.parts:
                part = cand.content.parts[0]
                if hasattr(part, "text"):
                    return part.text.strip()

        return ""

    except Exception as e:
        print("Erro API Gemini:", e)
        return ""



def interpretar_resposta(resposta, num_opcoes):
    clean = re.sub(r"[^\d\s]", " ", resposta)
    numeros = re.findall(r"\d+", clean)

    for n in numeros:
        num = int(n)
        if 1 <= num <= num_opcoes:
            return num
    return None


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://b.socrative.com/login/student/")
wait = WebDriverWait(driver, 120)


while True:
    try:
        esperar_pausa()

        # Captura pergunta
        question_element = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-text"))
        )
        question_text = question_element.text
        print("\nPergunta:", question_text)

        esperar_pausa()

        # Captura respostas
        answers_elements = wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "mc-answer-option-text"))
        )

        answers = [a.text.strip() for a in answers_elements]
        print(f"Foram encontradas {len(answers)} respostas.")

        for i, ans in enumerate(answers, start=1):
            print(f"{i}) {ans}")

        esperar_pausa()

        # Prompt para Gemini
        prompt = f"""
        Você é um modelo que responde perguntas de múltipla escolha.
        Responda APENAS com o número da opção correta.

        Pergunta: {question_text}

        Opções:
        {chr(10).join(f"{i+1}) {ans}" for i, ans in enumerate(answers))}

        Responda SOMENTE com o número (1-{len(answers)}).
        """

        resposta_texto = gerar_resposta_gemini(prompt)
        print("\nResposta bruta do Gemini:", resposta_texto)

        escolha = interpretar_resposta(resposta_texto, len(answers))

        if escolha:
            print(f"✔ Número sugerido: {escolha}")
            resposta_final = answers[escolha-1]
            print(f"✔ Resposta sugerida: {resposta_final}")

            esperar_pausa()

            # Clicar automaticamente
            try:
                answer_buttons = driver.find_elements(By.CLASS_NAME, "mc-answer-option")
                answer_buttons[escolha - 1].click()
                print("\n🟢 Resposta selecionada automaticamente.")
            except Exception as e:
                print("❌ Erro ao clicar na resposta:", e)

        else:
            print("❌ ERRO: Não consegui interpretar a resposta.")
            continue

        # Aguarda a próxima pergunta
        for _ in range(50):  # 10 segundos em intervalos de 0.2s
            esperar_pausa()
            time.sleep(0.2)

    except Exception as e:
        print("Erro geral:", e)
        print("Aguarde, tentando novamente…")
        time.sleep(5)
        continue

driver.quit()
