from fastapi.encoders import jsonable_encoder as original_jsonable_encoder

def custom_jsonable_encoder(obj, depth=0, max_depth=10, **kwargs):
    if depth > max_depth:
        return str(obj)
    
    if hasattr(obj, '__dict__'):
        return {k: custom_jsonable_encoder(v, depth=depth+1, max_depth=max_depth, **kwargs) 
                for k, v in obj.__dict__.items() 
                if not k.startswith('_')}
    elif isinstance(obj, (list, tuple)):
        return [custom_jsonable_encoder(item, depth=depth+1, max_depth=max_depth, **kwargs) for item in obj]
    else:
        return original_jsonable_encoder(obj, **kwargs)