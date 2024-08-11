# Setup Instructions for macOS

Follow these steps to set up the project environment on macOS:

1. **Clone the repository**:

   ```sh
   git clone https://github.com/nehiljain/lazypms.git
   cd lazypms
   ```

2. **Install Python 3.10**:
   Ensure you have Python 3.10 installed. You can use `pyenv` to manage Python versions:

   ```sh
   brew install pyenv
   pyenv install 3.10.0
   pyenv local 3.10.0
   ```

3. **Set up the virtual environment and install dependencies**:
   Use the `Makefile` to create the virtual environment and install dependencies:

   ```sh
   make install
   ```

4. **Activate the virtual environment**:
   Activate the virtual environment:

   ```sh
   source .venv/bin/activate
   ```

5. **Verify the setup**:
   Ensure everything is set up correctly by running:
   ```sh
   make lint
   ```

You are now ready to start working on the project!

## Available Makefile Commands

- `make install`: Set up the virtual environment and install dependencies.
- `make lint`: Lint the code using `flake8` and `black`.
- `make format`: Format the code using `black`.
- `make data`: Generate the dataset.
- `make clean`: Delete all compiled Python files.

For more details, refer to the `Makefile`.

Composio Apps: [https://app.composio.dev/apps?category=all](https://app.composio.dev/apps?category=all)
