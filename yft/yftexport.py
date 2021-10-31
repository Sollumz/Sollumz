import traceback


def export_yft(filepath):
    try:
        raise NotImplementedError
        return f"Succesfully exported : {filepath}"
    except:
        return f"Error exporting : {filepath} \n {traceback.format_exc()}"
