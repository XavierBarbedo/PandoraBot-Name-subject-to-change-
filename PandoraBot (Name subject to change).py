from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from gpt4all import GPT4All 
import os
import re

continua = True

# Carrega modelo local
model = GPT4All("mistral-7b-instruct-v0.2.Q4_0.gguf", model_path="./models")

# Inicializa Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://b.socrative.com/login/student/")  # URL do quiz

wait = WebDriverWait(driver, 15)

while continua:
    # Captura pergunta
    question_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "question-text")))
    question_text = question_element.text
    print("Pergunta:", question_text)

    # Captura todas as respostas
    answers_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "mc-answer-option-text")))
    answers_texts = [a.text for a in answers_elements]
    print(f"Foram encontradas {len(answers_texts)} respostas:")
    for idx, ans in enumerate(answers_texts, start=1):
        print(f"Resposta {idx}: {ans}")

    # Monta prompt estruturado para múltipla escolha
    prompt = f"""
Pergunta: {question_text}

Opções numeradas:
{chr(10).join(f"{i+1}) {ans}" for i, ans in enumerate(answers_texts))}

Escolha apenas o número da opção correta (1-{len(answers_texts)}). 
Não explique. Não invente respostas.
"""

    # Gera resposta
    response = model.generate(prompt, n_predict=50)
    
    # Extrai número da opção com regex
    match = re.search(r"\d+", response)
    if match:
        escolha = int(match.group())
        resposta_final = answers_texts[escolha-1]
    else:
        escolha = None
        resposta_final = "Não foi possível determinar a resposta."

    print(f"\nNúmero da opção sugerida pelo GPT4All: {escolha}")
    print(f"Resposta sugerida pelo GPT4All: {resposta_final}")

    # Espera input do utilizador antes da próxima pergunta
    input("Pressiona Enter para continuar para a próxima pergunta...")

# Fecha navegador ao terminar
driver.quit()
