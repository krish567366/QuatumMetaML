# quantummetaml/api/endpoints/pricing.py
@app.post("/pricing/select-model")
def select_pricing_model(model: str = Body(...)):
    config_manager.load_pricing_config(model)
    return {"status": f"Active pricing model: {model}"}

@app.get("/pricing/quote")
def get_quote(usage: dict):
    calculator = PricingCalculator(current_model())
    return calculator.generate_quote(usage)