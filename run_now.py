from springboard_engine import SpringboardAutomation

def run_now():
    print("🚀 Starting automation for requested course...")
    engine = SpringboardAutomation(
        email="sahu446688@gmail.com",
        password="Yash112233@",
        course_url="https://infyspringboard.onwingspan.com/web/en/app/toc/lex_auth_0127667384693882883448_shared/overview",
        headless=False,
        log_callback=lambda msg, level: print(f"[{level}] {msg}")
    )
    engine.run()
    print("✅ Finished!")

if __name__ == "__main__":
    run_now()
