from itertools import combinations
import sys
import time

def loadDataSet(file_path):
    # read file
    dataSet = open(file_path, 'r')
    data = []
    tmp = []
    now = 1
    # deal with IBM dataset, split with whitespace, combine products with same transaction id
    while True:
        string = dataSet.readline()
        if string == '':
            data.append(tmp)
            break
        customer, transaction, product = string.split()
        if now == transaction:
            tmp.append(product)
        else:
            data.append(tmp)
            tmp = [product]
            now = transaction
    return data

def generate_L1(data, min_support):
    count = {}
    # count every item appear times
    for transaction in data:
        for item in transaction:
            if item in count:
                count[item] += 1
            else:
                count[item] = 1
    total = len(data)
    L1 = []
    # calculate support, return L1 which support value is larger than min_support
    for item in count:
        if float(count[item])/total >= min_support:
            L1.append(item)
    L1.sort()
    return L1, count

def generate_subset(data):
    length = len(data)
    return list(combinations(data, length-1)) 

def apriori_gen(data):
    length = len(data)
    Ck = []
    for i in range(0, length):
        for j in range(i+1, length):
            if type(data[i]) is list:
                # two sets which (0, length-1) items are same, only last item different, combine
                if data[i][0:-1] == data[j][0:-1]:
                    tmp = data[i][0:-1]
                    tmp.append(data[i][-1])
                    tmp.append(data[j][-1])
                    Ck.append(tmp)
                else:
                    break
            # for set which has only one item
            else:
                tmp = []
                tmp.append(data[i])
                tmp.append(data[j])
                Ck.append(tmp)
    prune = []
    # check if candidate set's subsets are in last level candidate sets, if not remove it
    for item in Ck:
        subset = generate_subset(item)
        for s in subset:
            if len(s) == 1:
                s = s[0]
            else:
                s = list(s)
            if s not in data:
                prune.append(item)
                break
    for item in prune:
        Ck.remove(item)
    return Ck

def generate_rule(L, min_confidence, support):
    rules = {}
    confidences = {}
    L.reverse()
    for sets in L[1:-1]:
        for frequent_set in sets:
            # first get largest set's support value
            main_support = support[tuple(frequent_set)]
            length = len(frequent_set)
            # sets whose parents' set don't satisfy min_confidence
            redundant_set = []
            iter_set = list(combinations(frequent_set, length-1))
            # search form length-1 combinations to single item (top-down)
            for i in range(length-1, 0, -1):
                # remove redundant set from iterative set
                tmp = [item for item in iter_set if item not in redundant_set]
                del redundant_set[:]
                del iter_set[:]
                for x in tmp:
                    if len(x) == 1:
                        x = x[0]
                    # calculate current set's confidence value
                    confidence_value = float(main_support)/support[tuple(x)]
                    # satisfied min_support => rules
                    if confidence_value >= min_confidence:
                        rest = [item for item in frequent_set if item not in x]
                        if x not in rules:
                            rules[x] = [rest]
                            confidences[x] = [confidence_value]
                        else:
                            rules[x].append(rest)
                            confidences[x].append(confidence_value)
                        # put subsets into iterative set
                        subsets = list(combinations(x, i-1))
                        for subset in subsets:
                            if subset not in iter_set:
                                iter_set.append(subset)
                    # don't satisfied => ignore it's subsets, put into redundant sets
                    else:
                        subsets = list(combinations(x, i-1))
                        for subset in subsets:
                            if subset not in redundant_set:
                                redundant_set.append(subset)
                if len(iter_set) == 0:
                    break
    return rules, confidences

def apriori(file_path, argv1, argv2):
    # load data file
    data = loadDataSet(file_path)
    min_support = float(argv1)
    min_confidence = float(argv2)
    L = []
    # generate L1 set
    tmp_L, count = generate_L1(data, min_support)
    L.append(tmp_L)
    support = {}
    for x in count:
        support[tuple(x)] = count[x]
    k = 2
    total = len(data)
    while len(L[k-2]) != 0:
        # generate next level's frequent sets
        C_now = apriori_gen(L[k-2])
        length = len(C_now)
        count = [0 for x in range(0, length)]
        for t in data:
            for candidate in C_now:
                result = all(item in t for item in candidate)
                # if all items in candidate set also in transaction, count one time
                if result == True:
                    index = C_now.index(candidate)
                    count[index] += 1
        tmp = []
        pos = 0
        for num in count:
            # satisfied set
            if float(num)/total >= min_support:
                tmp.append(C_now[pos])
            # save support value
            support[tuple(C_now[pos])] = num
            pos += 1
        L.append(tmp)
        k += 1
    # generate rules with frequent sets
    rules, confidences = generate_rule(L, min_confidence, support)
    sort_dict = {}
    # sort with confidence value, use string as key, confidence value as value
    for left in rules:
        index = 0
        for right in rules[left]:
            tmp_str = str(left) + ' -> ' + str(right) + ' confidence: ' + str(confidences    [left][index])
            sort_dict[tmp_str] = confidences[left][index]
            index += 1
    # sort with value
    sort_dict = sorted(sort_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
    # output association rules
    for result in sort_dict:
        print result[0]

def main():
    if len(sys.argv) != 4:
        print 'Error format. python hw1_apriori.py [path_to_file] [min_support] [min_co    nfidence]'
        return
    # command line argument: file path, min_support, min_confidence
    # ex: python hw1_fp_growth.py dataset.data 0.5 0.5
    start = time.time()
    apriori(sys.argv[1], sys.argv[2], sys.argv[3])
    end = time.time()
    print 'spend time(s): ',end-start

if __name__ == '__main__':
    main()
