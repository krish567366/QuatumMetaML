# quantumml/api/main.py
from fastapi import FastAPI, Depends, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from .license.manager import LicenseValidator
from .quantum.optimizer import QuantumOptimizer, QuantumConfig
from .meta.learner import MetaLearner, MetaConfig
from .automl.engine import AutoMLEngine, AutoMLConfig
from .billing.processor import BillingManager, BillingConfig
import uvicorn

app = FastAPI(
    title="QuantumMetaML Enterprise API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url=None,
    servers=[{"url": "https://api.quantumml.com", "description": "Production"}]
)

# Security
app.add_middleware(HTTPSRedirectMiddleware)
security = APIKeyHeader(name="X-License-Key")

@app.on_event("startup")
async def startup():
    # Initialize shared components
    app.state.license_manager = LicenseValidator(os.getenv("LICENSE_MASTER_KEY"))
    app.state.billing_manager = BillingManager(
        BillingConfig(stripe_secret=os.getenv("STRIPE_KEY")),
        app.state.license_manager
    )

@app.post("/v1/train")
async def full_pipeline(
    request: Request,
    license_key: str = Depends(security),
    quantum_config: QuantumConfig = Depends(),
    meta_config: MetaConfig = Depends(),
    automl_config: AutoMLConfig = Depends()
):
    # License validation
    license_data = app.state.license_manager.validate_license(license_key, request.client.host)
    
    # Execute pipeline
    automl_engine = AutoMLEngine(automl_config, app.state.license_manager)
    quantum_optimizer = QuantumOptimizer(quantum_config, app.state.license_manager)
    meta_learner = MetaLearner(meta_config, app.state.license_manager)
    
    # Full training flow
    X, y = load_data(request.state.data_config)
    model = automl_engine.optimize(X, y)
    model = meta_learner.adapt(model, X, y)
    model = quantum_optimizer.optimize(model, X, y)
    
    return {"model_id": model.id, "accuracy": model.score(X, y)}

@app.post("/v1/billing/subscribe")
async def create_subscription(request: Request):
    return app.state.billing_manager.create_subscription(
        await request.json()
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, ssl_certfile="/etc/ssl/cert.pem")