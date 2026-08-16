DANGEROUS_TOOLS = {
    "run_shell",
    "delete_file",
    "delete_directory",
    "write_file",
    "install_package",
    "system_change",
}


def requires_confirmation(tool: str) -> bool:
    return tool in DANGEROUS_TOOLS


def ask_confirmation(description: str) -> bool:
    print()
    print("⚠️  CONFIRMATION REQUIRED")
    print(description)
    print()
    print("Type 'yes' to continue or anything else to cancel.")

    answer = input("> ").strip().lower()

    return answer in {
        "yes",
        "y",
    }
