#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Run the Streamlit application using 'python -m streamlit' for robustness.
# This ensures that streamlit is called via the Python interpreter that has it installed,
# which can help avoid PATH issues in some container environments.
# The 'exec' command replaces the shell process with the streamlit process,
# which is good practice for container entrypoint scripts as it allows signals
# to be passed correctly to the application.
exec python -m streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501}
