def compare_files(fp1, fp2):
    """
    Function that compares two target files
    Parameters
    ----------
    fp1 : open file pointer
        pointer to open first file
    fp2 : open file pointer
        pointer to open second file
    
    Returns
    -------
    True if they are the same, false otherwise
    """

    line1 = fp1.readline()
    line2 = fp2.readline()

    while line1 and line2:
        if line1.startswith('#') and line2.startswith('#'):
            pass
        elif not line1 == line2:
            return False
        
        line1 = fp1.readline()
        line2 = fp2.readline()

    if line1 or line2:
        return False

    return True

