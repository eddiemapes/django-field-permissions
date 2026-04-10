def has_field_perm(request, model_name, field_name, access_level):
    # Superuser override check 
    if request.user.is_superuser:
        return True

    # If field permissions are not attached via middleware, return False 
    if not hasattr(request, 'field_perms'):
        return False
    
    # Return True/False if user has field-level permission 
    return (model_name, field_name, access_level) in request.field_perms
