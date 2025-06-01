# Trabalho CP3A - Exploração de Ferramenta de Visão Computacional (YOLO)

## Instituição

- **Instituto Politécnico de Viana do Castelo - Escola Superior de Tecnologia e Gestão (IPVC - ESTG)**

## Docentes Orientadores

- **Professor Doutor Jorge Ribeiro**

- **Professor Doutor Abel Dantas**

## Unidade Curricular

- **Aprendizagem Organizacional**

## Ano Letivo

- **2024/2025**

## Aluno

- **Luís Vale do Carmo**, Aluno N.º29341

## Descrição do Projecto

Este projeto implementa um detetor de frutas utilizando YOLOv5 com uma interface gráfica intuitiva desenvolvida em PySide6. A aplicação permite o processamento de imagens e vídeos para deteção automática de frutas, análise de qualidade e informação nutricional detalhada.

## Funcionalidades Principais

1. **Deteção de Frutas em Tempo Real**
   - Identificação precisa de diferentes tipos de frutas
   - Visualização em tempo real com bounding boxes
   - Indicadores de confiança para cada deteção

2. **Análise de Qualidade**
   - Avaliação do nível de maturação
   - Deteção de defeitos
   - Estimativa de peso
   - Recomendações de armazenamento

3. **Informação Nutricional**
   - Calorias
   - Proteínas
   - Carboidratos
   - Fibras
   - Vitaminas

4. **Interface Intuitiva**
   - Visualização lado a lado (imagem original/deteção)
   - Abas para análise detalhada
   - Geração de relatórios em PDF

## Screenshots

### 1. Interface Principal
![Interface Principal](images/new_image.jpeg)

### 2. Análise de Qualidade
![Análise de Qualidade](images/new_image2.png)

### 3. Informação Nutricional
![Informação Nutricional](images/new_image3.png)

### 4. Excerto do Relatório
![Excerto do Relatório](images/new_image4.png)

## Configuração do Ambiente

### Pré-requisitos

- **Sistema Operativo**: Linux, Windows ou MacOS
- **Python**: Versão 3.6 ou superior
- **PyTorch**: Versão 1.7 ou superior

### Instruções de Configuração

1. Clone o repositório:
   ```bash
   git clone https://github.com/luisvc004/CP3A_Fruit-Detector.git
   
   cd CP3A_Fruit-Detector
   ```
   
2. Instale as dependências necessárias:
    ```bash
   pip install -r requirements.txt
    ```

3. Descarregue o modelo treinado:

- Faça o download através deste link: [Modelo YOLOv5 Fruits](https://drive.google.com/file/d/1W6qZeutnqnp3YX9w4iYgR44xsoi_64ff/view?usp=sharing)
- Coloque o ficheiro descarregado no diretório `weights/`

4. Execute a aplicação:

```bash
python main.py
```

## Configuração Local (Ambiente Virtual)

Para uma instalação isolada utilizando ambiente virtual (recomendado):

```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
python3 main.py
```

## Dataset

O conjunto de dados utilizado para treino está disponível [aqui](https://t.ly/NZWj).

## Resolução de Problemas

- **Mac/Linux**: Utilize preferencialmente o método de instalação com ambiente virtual
- **Problemas de dependências**: Certifique-se de que tem Python 3.6+ e PyTorch 1.7+ instalados
- **Erro ao carregar modelo**: Verifique se o ficheiro do modelo está no diretório `weights/`

## Contribuições

Este projeto foi desenvolvido com base no YOLOv5 e adaptado para deteção específica de frutas, incluindo:
- Análise de qualidade e maturação
- Informação nutricional detalhada
- Interface gráfica intuitiva
- Geração de relatórios em PDF