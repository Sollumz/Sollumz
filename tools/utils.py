
class StringHelper():

    @staticmethod
    def FixShaderName(name):
        if("." in name):
            name = name[:-4]
        return name


class ListHelper():

    @staticmethod
    def divide_list(list, d):
        result = []
        for item in list:
            answer = item / d
            result.append(answer)
        return result
