#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Run the Streamlit application using 'python3 -m streamlit' for robustness.
# This ensures that streamlit is called via the Python 3 interpreter that has it installed,
# which can help avoid PATH issues or version conflicts in some container environments.
# The 'exec' command replaces the shell process with the streamlit process,
# which is good practice for container entrypoint scripts as it allows signals
# to be passed correctly to the application.
exec python3 -m streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501}
