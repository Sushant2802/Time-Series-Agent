# 🤖 Aivee - Time Series Analysis Agent

Aivee is a tool-based AI agent that analyzes time-series data using LLM + Python tools.

It ensures **accurate results** by always using tools (no hallucination).

---

## 🚀 What It Does

- 📊 Calculate stats (mean, median, percentile)
- 📈 Generate plots (line, bar, histogram)
- 🔍 Filter data (>, <, range)
- 🔗 Chain operations (stats → plot)
- 🧠 Use memory (context-aware queries)

---

## 🏗️ How It Works

User → Agent → LLM (Converse) → Tools → Data → Output

- Agent detects intent
- LLM decides which tool to call
- Tools perform actual computation
- Output is returned (stats / plots)

---

## 📂 Project Structure

agent.py   → Agent logic  
config.py  → Model + prompt  
main.py    → CLI app  
tools.py   → Stats, Plot, Filter  
store.py   → Load dataset  
utils.py   → Helpers  

data/      → CSV file  
plots/     → Generated graphs  

---

## ▶️ Run

```bash
python main.py
```

---

## 💬 Example Queries

- give mean of pressure
- plot temperature line
- show 90 percentile
- plot above 80 percentile

---

## ⚡ Key Concepts

- Tool-based execution → no fake answers  
- Threshold logic → accurate percentile filtering  
- Tool chaining → stats → plot  
- Context memory → no repeated inputs  

---

## ⚠️ Challenges Solved

- Time-based filtering (datetime handling)
- Correct count after threshold filtering
- Prompt tuning for correct tool calling
- Passing data between tools (no recompute)

---

## 🛠 Tech Stack

- Python  
- LangGraph (ReAct Agent)  
- AWS Bedrock (Claude - Converse API)  
- Pandas, NumPy, Matplotlib, Plotly

---

## 👨‍💻 Author

**Sushant Mane** 

_AI Engineer_  
📧 **sushantm1210@gmail.com**

