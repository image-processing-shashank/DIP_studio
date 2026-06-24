"""Runtime configuration. Override any value with an environment variable."""
import os

# Maximum accepted upload size in megabytes.
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "600"))

# Very large images are downsampled to this longest-edge size before
# processing, so heavy operations (FFT, large kernels) stay responsive
# regardless of the uploaded resolution. Set to 0 to disable.
MAX_PROCESS_DIM = int(os.getenv("MAX_PROCESS_DIM", "2000"))

# Returned preview images are capped at this longest edge to limit payload.
MAX_DISPLAY_DIM = int(os.getenv("MAX_DISPLAY_DIM", "1600"))

# Comma-separated list of allowed CORS origins for the frontend.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
