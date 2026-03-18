# 🎮 Nomi, Cose, Città - Distributed Multiplayer Game

A real-time, distributed implementation of the classic Italian word game "Nomi, Cose, Città" (Names, Things, Cities) built with Python.

## 📝 Project Overview

This project reimagines the traditional pen-and-paper game as a modern multiplayer experience where players compete in real-time to find words matching specific categories and starting letters. The game features a distributed architecture with both client-server and peer-to-peer communication, ensuring robust gameplay with fault tolerance and consistency across all nodes.

## 🚀 Getting Started

### Prerequisites
To run this project, you will need:
- **Python 3.10** (or higher)
- **Poetry**

### Installation
Clone the repository and install the required dependencies using Poetry: 

```bash
poetry install
```

### Start the server
Open a terminal and run the primary game server:

```bash
poetry run python nomicosecitta/src/server/main.py
```

Launch the exact same command on a secondary terminal to instantiate a Backup server. If you want more backup server, launch multiple terminal.

### Launch the Client
On the players' machines, start the graphical client

```bash
poetry run python nomicosecitta/src/client/main.py
```

## 🎯 How to Play

1. **Join the game**: Connect to the server
2. **Lobby & Configuration**: The administrator configures the game mode, then starts
   the match for all participants in the lobby.
3. **Game Round**: 
   - A random letter are presented
   - Write words starting with that letter for each category
   - Submit your answers before time runs out
4. **Validation Phase**:
   - Review other players' answers
   - Vote to accept or reject each answer
   - Chat with other players to discuss answers
5. **Scoring**: Points are awarded for validated answers
6. **Victory**: First player to reach the target score wins!

## 👥 Team

- **Chiara Giangiulli** - chiara.giangiulli@studio.unibo.it
- **Giovanni Pisoni** - giovanni.pisoni@studio.unibo.it
- **Dilaver Shtini** - dilaver.shtini@studio.unibo.it

## 🙏 Acknowledgments

- Inspired by the classic Italian game "Nomi, Cose, Città"
- Built as part of the Distributed Systems course at University of Bologna

**Happy Gaming! 🎉**

## 📄 Report

For a more in-depth analysis of the architecture, networking, and fault-tolerance mechanisms, please read our [official project report](https://github.com/ChiaraGiangiulli/ds-report).
