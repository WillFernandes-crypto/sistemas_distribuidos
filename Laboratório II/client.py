import rpyc


def main():
    conn = rpyc.connect("localhost", 8001)
    try:
        current_time = conn.root.get_time()
        print(f"Horário do servidor: {current_time}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
