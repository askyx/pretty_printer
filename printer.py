import gdb
import string

printer = gdb.printing.RegexpCollectionPrettyPrinter("PostgreSQL 16beta2")

class printerRtes(gdb.Parameter):
    def __init__(self) -> None:
        super(printerRtes, self).__init__('pg_retes', gdb.COMMAND_DATA, gdb.PARAM_STRING)
        self.value = 'None'
        self.rtes = None

    def get_set_string(self) -> str:
        if self.value == 'None':
            return ''
        self.rtes = gdb.parse_and_eval(self.value)
        node = cast(self.rtes, 'List').dereference()
        print(node)
        return ''

    def get_show_string(self, svalue: str) -> str:
        if self.rtes != None:
            node = cast(self.rtes, 'List').dereference()
            print(node)
        return ''

    def get_rte(self, index: int) -> gdb.Value:
        node = cast(self.rtes, 'List')
        return node['elements'][index - 1]

class printerTurn(gdb.Parameter):
    def __init__(self) -> None:
        super(printerTurn, self).__init__('pg_print', gdb.COMMAND_DATA, gdb.PARAM_BOOLEAN)
        self.value = True

    def get_set_string(self) -> str:
        if self.value == False:
            for p in printer.subprinters:
                p.enabled = False
        else:
            for p in printer.subprinters:
                p.enabled = True

        return ''

rtes = printerRtes()
printerTurn()

class PgType:
    def __init__(self) -> None:
        self.types = {}
        with open('/home/asky/pretty_printer/pg_type.txt') as file:
            for line in file:
                kv = line.strip().split()
                if len(kv) != 0:
                    self.types[int(kv[0])] = kv[2]

    def get_type(self, key: int) -> str:
        if key in self.types:
            return self.types[key]
        else:
            return 'unkowne_type'

class PgOperator:
    def __init__(self) -> None:
        self.oper = {}
        with open('/home/asky/pretty_printer/pg_operator.txt') as file:
            for line in file:
                kv = line.strip().split()
                if len(kv) != 0:
                    self.oper[int(kv[0])] = kv[2]

    def get_oper(self, key: int) -> str:
        if key in self.oper:
            return self.oper[key]
        else:
            return 'unkowne_oper'

pg_type = PgType()
pg_oper = PgOperator()

def register_printer(name):
    def __registe(_printer):
        printer.add_printer(name, '^' + name + '$', _printer)
    return __registe

def get_node_type(node):
    type = str(node['type'])[2:]
    if type == 'Bitmapset':
        return 'Relids'
    return type

# max print 100
def getchars(arg, qoute = True, len = 100):
    if (str(arg) == '0x0'):
        return str(arg)

    retval = ''
    if qoute:
        retval += '\''

    i=0
    while arg[i] != ord("\0") and i < len:
        character = int(arg[i].cast(gdb.lookup_type("char")))
        if chr(character) in string.printable:
            retval += "%c" % chr(character)
        else:
            retval += "\\x%x" % character
        i += 1

    if qoute:
        retval += '\''

    return retval

def cast(node, type_name):
    t = gdb.lookup_type(type_name)
    return node.cast(t.pointer())

class ListIt(object):
    def __init__(self, list) -> None:
        self.elements = list['elements']
        self.size = list['length']
        self.count = 0

    def __iter__(self):
        return self

    def __len__(self):
        return int(self.size)

    def __next__(self):
        if self.count == self.size:
            raise StopIteration

        result = self.elements[self.count]
        self.count += 1

        return result

def add_list(list, val, filde):
    if str(val[filde]) != '0x0':
        list.append((filde, val[filde].dereference()))

def plan_to_string(type, plan):
    return '%s (cost=%.2f..%.2f rows=%.0f width=%.0f plan_node_id=%s)' %(
        type,
        float(plan['startup_cost']),
        float(plan['total_cost']),
        float(plan['plan_rows']),
        float(plan['plan_width']),
        plan['plan_node_id']
    )

def plan_children(plan):
    list = []
    if gdb.parameter('pg_verbose'):
        add_list(list, plan, 'targetlist')
    add_list(list, plan, 'qual')
    add_list(list, plan, 'initPlan')
    add_list(list, plan, 'lefttree')
    add_list(list, plan, 'righttree')
    return list

def path_to_string(type, path):
    '''
    print path
    '''
    return '%s %s (cost=%.2f..%.2f rows=%.0f)' %(
        type,
        path['pathtype'],
        float(path['startup_cost']),
        float(path['total_cost']),
        float(path['rows'])
    )

def path_children(path):
    list = []
    add_list(list, path, 'pathtarget')
    add_list(list, path, 'param_info')
    add_list(list, path, 'pathkeys')
    return list

class Printer:
    def __init__(self, val) -> None:
        self.val = val

    def to_string_pretty(self, name, *args):
        ret = '%s' % name
        if len(args) != 0:
            ret += '['

        ss = []
        for arg in args:
            s = '%s: %s' % (arg, self.val[arg])
            ss.append(s)

        ret += ', '.join(ss)

        if len(args) != 0:
            ret += ']'

        return ret

    def children_pretty(self, *args):
        list = []
        for arg in args:
            add_list(list, self.val, arg)
        return list

@register_printer('Query')
class QueryPrinter(Printer):
    def to_string(self):
        return str(self.val['commandType'])

    def children(self):
        return self.children_pretty('cteList' ,'utilityStmt' ,'rtable' ,'jointree' ,'targetList' ,'onConflict' ,'returningList' ,'groupClause' ,'groupingSets' ,'havingQual' ,'windowClause' ,'distinctClause' ,'sortClause' ,'limitOffset' ,'rowMarks' ,'setOperations' ,'constraintDeps' ,'withCheckOptions')

@register_printer('List')
class ListPrinter:
    'print List'
    class _iter(object):
        def __init__(self, it, type) -> None:
            self.it = it
            self.type = type
            self.count = 0

        def __iter__(self):
            return self

        def __next__(self):
            node = next(self.it)
            if str(self.type) == 'List':
                try:
                    node = cast(node['ptr_value'], 'Node').dereference()
                except:
                    # TODO
                    node = cast(node['ptr_value'], 'ReduceInfo').dereference()
            elif str(self.type) == 'IntList':
                node = int(node['int_value'])
            else:
                node = int(node['oid_value'])

            result = (str(self.count), node)
            self.count += 1
            return result


    def __init__(self,  val) -> None:
        self.val = val
        self.type = str(self.val['type'])[2:]

    def to_string(self):
        return '%s with %s elements' % (self.type, self.val['length'])

    def children(self):
        return self._iter(ListIt(self.val), self.type)

    def display_hint(self):
        if self.type == 'List':
            return None
        else:
            return 'array'

@register_printer('Node')
class NodePrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        type = get_node_type(self.val)
        if type == 'A_Star':
            return '*'
        return self.val.address.cast(gdb.lookup_type(type).pointer()).dereference()

@register_printer('Expr')
class ExprPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        type = get_node_type(self.val)
        return self.val.address.cast(gdb.lookup_type(type).pointer()).dereference()

@register_printer('Path')
class PathPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        type = get_node_type(self.val)
        return self.val.address.cast(gdb.lookup_type(type).pointer()).dereference()

@register_printer('ProjectionPath')
class ProjectionPathPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <dummypp: %s>' % (
            str(self.val['dummypp']),
        )
        return path_to_string('ProjectionPath', self.val['path']) + ext

    def children(self):
        list = path_children(self.val['path'])
        add_list(list, self.val, 'subpath')
        return list

@register_printer('Relids')
class RelidsPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        l = int(self.val['nwords'])
        ret = ''
        while l > 0:
            l -= 1
            ret = str(self.val['words'][l]) + ' ' + ret
        return 'Relids:' + ret

@register_printer('FuncExpr')
class FuncExprPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('FuncExpr', 'funcid' ,'funcresulttype' ,'funcretset' ,'funcvariadic' ,'funcformat' ,'funccollid' ,'inputcollid')

    def children(self):
        return self.children_pretty('args')

@register_printer('RowExpr')
class RowExprPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('RowExpr', 'row_typeid', 'row_format')

    def children(self):
        return self.children_pretty('args', 'colnames')

@register_printer('ParamRef')
class ParamRefPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('ParamRef', 'number')

@register_printer('ColumnRef')
class ColumnRefPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        fields = cast(self.val['fields'], 'List')
        l = fields['length']
        col = ''
        while l > 0:
            l -= 1
            item = cast(fields['elements'][l]['ptr_value'], 'Node')
            s = '.%s' % item.dereference()
            col = s + col

        if gdb.parameter('pg_verbose') == True:
            return 'ColumnRef[location: %s]' % (
                self.val['location'],
            )
        else:
            return "ColumnRef['%s']" % col

    def children(self):
        list = []
        if gdb.parameter('pg_verbose') == True:
            add_list(list, self.val, 'fields')
        return list

@register_printer('ResTarget')
class ResTargetPrinter(Printer):
    def to_string(self):
        return 'ResTarget[name: %s]' % (
            getchars(self.val['name'], False),
        )

    def children(self):
        return self.children_pretty('indirection', 'val')

@register_printer('ValUnion')
class ValUnionPrinter(Printer):
    def to_string(self):
        vt = str(self.val['node']['type'])[2:]
        ret = ''
        if vt == 'Integer':
            ret += str(self.val['ival']['ival'])
        elif vt == 'Float':
            ret += getchars(self.val['fval']['fval'])
        elif vt == 'Boolean':
            ret += str(self.val['boolval']['boolval'])
        elif vt == 'BitString':
            ret += getchars(self.val['bsval']['bsval'])
        elif vt == 'String':
            ret += getchars(self.val['sval']['sval'])
        return '%s[ %s ]' % (
            vt,
            ret
        )

@register_printer('A_Const')
class A_ConstPrinter(Printer):
    def to_string(self):
        return 'A_Const[ %s ]' % (
            self.val['val'],
        )

@register_printer('CollateClause')
class CollateClausePrinter(Printer):
    def to_string(self):
        return 'CollateClause'

    def children(self):
        return self.children_pretty('arg', 'collname')

@register_printer('RoleSpec')
class RoleSpecPrinter(Printer):
    def to_string(self):
        return 'RoleSpec[roletype: %s, rolename: %s]' % (
            self.val['roletype'],
            getchars(self.val['rolename'])
        )

@register_printer('FuncCall')
class FuncCallPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('FuncCall', 'agg_within_group' ,'agg_star' ,'agg_distinct' ,'func_variadic' ,'funcformat')

    def children(self):
        return self.children_pretty('funcname', 'args', 'agg_order', 'agg_filter', 'over')

@register_printer('A_Indices')
class A_IndicesPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('A_Indices', 'is_slice')

    def children(self):
        return self.children_pretty('lidx', 'uidx')

@register_printer('A_Indirection')
class A_IndirectionPrinter(Printer):
    def to_string(self):
        return 'A_Indirection'

    def children(self):
        return self.children_pretty('arg', 'indirection')

@register_printer('A_ArrayExpr')
class A_ArrayExprPrinter(Printer):
    def to_string(self):
        return 'A_ArrayExpr'

    def children(self):
        return self.children_pretty('elements')

@register_printer('MultiAssignRef')
class MultiAssignRefPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        return 'MultiAssignRef[colno: %s]' % (
            self.val['colno'],
        )

    def children(self):
        list = []
        add_list(list, self.val, 'source')
        return list

@register_printer('SortBy')
class SortByPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        return 'SortBy[sortby_dir: %s, sortby_nulls: %s]' % (
            self.val['sortby_dir'],
            self.val['sortby_nulls'],
        )

    def children(self):
        list = []
        add_list(list, self.val, 'node')
        add_list(list, self.val, 'useOp')
        return list

@register_printer('WindowDef')
class WindowDefPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        return 'WindowDef[name: %s, refname: %s, frameOptions: %s]' % (
            getchars(self.val['name']),
            getchars(self.val['refname']),
            self.val['frameOptions'],
        )

    def children(self):
        list = []
        add_list(list, self.val, 'partitionClause')
        add_list(list, self.val, 'orderClause')
        add_list(list, self.val, 'startOffset')
        add_list(list, self.val, 'endOffset')
        return list

@register_printer('RangeSubselect')
class RangeSubselectPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        return 'RangeSubselect[lateral: %s]' % (
            self.val['lateral'],
        )

    def children(self):
        list = []
        add_list(list, self.val, 'subquery')
        add_list(list, self.val, 'alias')
        return list

@register_printer('RangeFunction')
class RangeFunctionPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        return 'RangeFunction[lateral: %s, ordinality: %s, is_rowsfrom: %s]' % (
            self.val['lateral'],
            self.val['ordinality'],
            self.val['is_rowsfrom'],
        )

    def children(self):
        list = []
        add_list(list, self.val, 'functions')
        add_list(list, self.val, 'alias')
        add_list(list, self.val, 'coldeflist')
        return list

@register_printer('RangeTableFunc')
class RangeTableFuncPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        return 'RangeTableFunc[lateral: %s]' % (
            self.val['lateral'],
        )

    def children(self):
        list = []
        add_list(list, self.val, 'docexpr')
        add_list(list, self.val, 'rowexpr')
        add_list(list, self.val, 'namespaces')
        add_list(list, self.val, 'columns')
        add_list(list, self.val, 'alias')
        return list

@register_printer('RangeTableFuncCol')
class RangeTableFuncColPrinter(Printer):
    def to_string(self):
        return 'RangeTableFuncCol[colname: %s, for_ordinality: %s, is_not_null: %s]' % (
            getchars(self.val['colname']),
            self.val['for_ordinality'],
            self.val['is_not_null'],
        )

    def children(self):
        list = []
        add_list(list, self.val, 'typeName')
        add_list(list, self.val, 'colexpr')
        add_list(list, self.val, 'coldefexpr')
        return list

@register_printer('RangeTableSample')
class RangeTableSamplePrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        return 'RangeTableSample'

    def children(self):
        list = []
        add_list(list, self.val, 'relation')
        add_list(list, self.val, 'method')
        add_list(list, self.val, 'args')
        add_list(list, self.val, 'repeatable')
        return list

@register_printer('ColumnDef')
class ColumnDefPrinter(Printer):
    def to_string(self):
        return 'ColumnDef[colname: %s, compression: %s, inhcount: %s, is_local: %s, is_not_null: %s, is_from_type: %s, storage: %s, identity: %s, generated: %s, collOid: %s]' % (
            getchars(self.val['colname']),
            getchars(self.val['compression']),
            self.val['inhcount'],
            self.val['is_local'],
            self.val['is_not_null'],
            self.val['is_from_type'],
            self.val['storage'],
            self.val['identity'],
            self.val['generated'],
            self.val['collOid'],
        )

    def children(self):
        return self.children_pretty('typeName' ,'raw_default' ,'cooked_default' ,'identitySequence' ,'collClause' ,'constraints' ,'fdwoptions')

@register_printer('TableLikeClause')
class TableLikeClausePrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('TableLikeClause', 'options', 'relationOid')

    def children(self):
        return self.children_pretty('relation')

@register_printer('IndexElem')
class IndexElemPrinter(Printer):
    def to_string(self):
        return 'IndexElem[name: %s, indexcolname: %s, ordering: %s, nulls_ordering: %s]' % (
            getchars(self.val['name']),
            getchars(self.val['indexcolname']),
            self.val['ordering'],
            self.val['nulls_ordering'],
        )

    def children(self):
        return self.children_pretty('expr' ,'collation' ,'opclass' ,'opclassopts' ,'expr')

@register_printer('DefElem')
class DefElemPrinter(Printer):
    def to_string(self):
        return 'DefElem[defnamespace: %s, defname: %s, defaction: %s]' % (
            getchars(self.val['defnamespace']),
            getchars(self.val['defname']),
            self.val['defaction'],
        )

    def children(self):
        return self.children_pretty('arg')

@register_printer('LockingClause')
class LockingClausePrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('LockingClause', 'strength', 'waitPolicy')

    def children(self):
        return self.children_pretty('lockedRels')

@register_printer('XmlSerialize')
class XmlSerializePrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('XmlSerialize', 'xmloption', 'indent')

    def children(self):
        return self.children_pretty('expr', 'typeName')

@register_printer('A_Expr')
class A_ExprPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('A_Expr', 'kind')

    def children(self):
        return self.children_pretty('name', 'lexpr', 'rexpr')

@register_printer('RangeVar')
class RangeVarPrinter(Printer):
    def to_string(self):
        strs = ''
        if str(self.val['catalogname']):
            strs += '%s.' % getchars(self.val['catalogname'], False)
        if str(self.val['schemaname']):
            strs += '%s.' % getchars(self.val['schemaname'], False)
        if str(self.val['relname']):
            strs += '%s' % getchars(self.val['relname'], False)
        return 'RangeVar[%s, inh: %s, relpersistence: %s]' % (
            strs,
            self.val['inh'],
            self.val['relpersistence'],
        )

    def children(self):
        return self.children_pretty('alias')

@register_printer('SelectStmt')
class SelectStmtPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('SelectStmt', 'groupDistinct', 'op', 'all', 'limitOption')

    def children(self):
        return self.children_pretty('distinctClause' ,'intoClause' ,'targetList' ,'fromClause' ,'whereClause' ,'groupClause' ,'havingClause' ,'windowClause' ,'valuesLists' ,'sortClause' ,'limitOffset' ,'limitCount' ,'lockingClause' ,'withClause' ,'larg' ,'rarg')
        # if str(self.val['limitOffset']) != '0x0' or str(self.val['limitCount']) != '0x0':
        #     list.append(('limitOption', self.val['limitOption']))

@register_printer('RowCompareExpr')
class RowCompareExprPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('RowCompareExpr', 'rctype')

    def children(self):
        return self.children_pretty('opnos' ,'opfamilies' ,'inputcollids' ,'largs' ,'rargs')

@register_printer('AlternativeSubPlan')
class AlternativeSubPlanPrinter(Printer):
    def to_string(self):
        return 'AlternativeSubPlan'

    def children(self):
        return self.children_pretty('subplans')

@register_printer('TypeCast')
class TypeCastPrinter(Printer):
    def to_string(self):
        return 'TypeCast'

    def children(self):
        return self.children_pretty('arg', 'typeName')

@register_printer('TypeName')
class TypeNamePrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('TypeName', 'typeOid', 'setof', 'pct_type', 'typemod')

    def children(self):
        return self.children_pretty('names', 'typmods', 'arrayBounds')

@register_printer('Alias')
class AliasPrinter(Printer):
    def to_string(self):
        return 'Alias[aliasname: %s]' % (
            getchars(self.val['aliasname'])
        )

    def children(self):
        return self.children_pretty('colnames')

@register_printer('RawStmt')
class RawStmtPrinter(Printer):
    def to_string(self):
        return 'RawStmt'

    def children(self):
        return self.children_pretty('stmt')

@register_printer('SubLink')
class SubLinkPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('SubLink', 'subLinkType', 'subLinkId')

    def children(self):
        return self.children_pretty('testexpr', 'operName', 'subselect')

@register_printer('FieldSelect')
class FieldSelectPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('FieldSelect', 'fieldnum', 'resulttype', 'resulttypmod', 'resultcollid')

    def children(self):
        return self.children_pretty('arg')

@register_printer('FieldStore')
class FieldStorePrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('FieldStore', 'resulttype')

    def children(self):
        return self.children_pretty('arg', 'newvals', 'fieldnums')

@register_printer('SubscriptingRef')
class SubscriptingRefPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('SubscriptingRef', 'refcontainertype' ,'refelemtype' ,'reftypmod' ,'refcollid')

    def children(self):
        return self.children_pretty('args', 'refupperindexpr', 'reflowerindexpr', 'refexpr', 'refassgnexpr')

@register_printer('CoalesceExpr')
class CoalesceExprPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('CoalesceExpr', 'coalescetype', 'coalescecollid')

    def children(self):
        return self.children_pretty('args')

@register_printer('CaseExpr')
class CaseExprPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('CaseExpr', 'casetype', 'casecollid')

    def children(self):
        return self.children_pretty('arg', 'args', 'defresult')

@register_printer('Param')
class ParamPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('Param', 'paramkind' ,'paramid' ,'paramtype' ,'paramtypmod' ,'paramcollid')

@register_printer('PlannerParamItem')
class PlannerParamItemPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('PlannerParamItem', 'paramId')

    def children(self):
        return self.children_pretty('item')

@register_printer('RestrictInfo')
class RestrictInfoPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('RestrictInfo', 'is_pushed_down' ,'outerjoin_delayed' ,'can_join' ,'pseudoconstant' ,'leakproof' ,'security_level' ,'clause_relids' ,'required_relids' ,'outer_relids' ,'nullable_relids' ,'left_relids' ,'right_relids' ,'eval_cost')

    def children(self):
        return self.children_pretty('clause' ,'orclause' ,'parent_ec' ,'mergeopfamilies' ,'left_ec' ,'right_ec' ,'left_em' ,'right_em' ,'scansel_cache')

@register_printer('CaseWhen')
class CaseWhenPrinter(Printer):
    def to_string(self):
        return 'CaseWhen'

    def children(self):
        return self.children_pretty('expr', 'result')

@register_printer('TargetEntry')
class TargetEntryPrinter(Printer):
    def to_string(self):
        return 'TargetEntry[resname: %s, resno: %s, ressortgroupref: %s, resorigtbl: %s, resorigcol: %s]' % (
            getchars(self.val['resname']),
            self.val['resno'],
            self.val['ressortgroupref'],
            self.val['resorigtbl'],
            self.val['resorigcol']
        )

    def children(self):
        return {
            ('expr', self.val['expr'].dereference()),
        }

    def display_hint(self):
        return 'array'

@register_printer('RangeTblEntry')
class RangeTblEntryPrinter(Printer):
    def to_string(self):
        alias = self.val['eref'].dereference()
        retval = 'RangeTblEntry: [kind: %-17s' % (self.val['rtekind'])
        if str(alias['aliasname']) != '0x0': retval += ', alias: %-17s' % getchars(alias['aliasname'])
        retval += ', relid: %8s' % self.val['relid']
        retval += ', relkind: %s' % ((self.val['relkind']))
        retval += ']'
        return retval

    def children(self):
        if gdb.parameter('pg_verbose') == False:
            return []
        cols = self.val['eref'].dereference()['colnames']
        if str(cols) != '0x0':
            return {('cols', cols.dereference())}
        else:
            return {('cols', 'List with 0 elements')}

@register_printer('SortGroupClause')
class SortGroupClausePrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('SortGroupClause', 'tleSortGroupRef', 'eqop', 'sortop', 'nulls_first', 'hashable')

@register_printer('FromExpr')
class FromExprPrinter(Printer):
    def to_string(self):
        return 'FromExpr'

    def children(self):
        return self.children_pretty('fromlist' ,'quals')

@register_printer('JoinExpr')
class JoinExprPrinter(Printer):
    def to_string(self):
        return '[jointype: %s, isNatural: %s, rtindex: %s]' % (self.val['jointype'], self.val['isNatural'], self.val['rtindex'])

    def children(self):
        return self.children_pretty('larg' ,'rarg' ,'usingClause' ,'quals' ,'alias')

@register_printer('RangeTblRef')
class RangeTblRefPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('RangeTblRef', 'rtindex')

@register_printer('Integer')
class IntegerPrinter(Printer):
    def to_string(self):
        return self.val['ival']

@register_printer('Float')
class FloatPrinter(Printer):
    def to_string(self):
        return self.val['fval']

@register_printer('Boolean')
class BooleanPrinter(Printer):
    def to_string(self):
        return self.val['boolval']

@register_printer('String')
class StringPrinter(Printer):
    def to_string(self):
        return getchars(self.val['sval'], False)

@register_printer('BitString')
class BitStringPrinter(Printer):
    def to_string(self):
        return getchars(self.val['bsval'], False)

@register_printer('BoolExpr')
class BoolExprPrinter(Printer):
    def to_string(self):
        if rtes.rtes != None:
            list = cast(self.val['args'], 'List')
            len = int(list['length'])
            op = str(self.val['boolop'])
            expr = '('
            if op == 'NOT_EXPR':
                op += 'NOT '
            expr += str(cast(list_nth(list, 0, 'ptr'), 'Node').dereference())
            i = 1
            while i < len:
                if op == 'AND_EXPR':
                    expr += ' AND '
                elif op == 'OR_EXPR':
                    expr += ' OR '
                expr += str(cast(list_nth(list, i, 'ptr'), 'Node').dereference())
                i += 1

            expr += ')'
            return expr
        else:
            return 'boolop: %s' % self.val['boolop']

    def children(self):
        list = []
        if rtes.rtes == None:
            add_list(list, self.val, 'args')
        return list

@register_printer('OpExpr')
class OpExprPrinter(Printer):
    def to_string(self):
        if rtes.rtes != None:
            list = cast(self.val['args'], 'List')
            if int(list['length']) == 2:
                return '(%s %s %s)' % (
                    cast(list_nth(list, 0, 'ptr'), 'Node').dereference(),
                    pg_oper.get_oper(int(self.val['opno'])),
                    cast(list_nth(list, 1, 'ptr'), 'Node').dereference()
                )
            else:
                return '(%s %s)' % (
                   pg_oper.get_oper(int(self.val['opno'])),
                   cast(list_nth(list, 0, 'ptr'), 'Node').dereference()
                )
        else:
            return 'OpExpr[opno: %s, opfuncid: %s, opresulttype: %s, opretset %s, opcollid %s, inputcollid %s]' % (
                self.val['opno'],
                self.val['opfuncid'],
                self.val['opresulttype'],
                self.val['opretset'],
                self.val['opcollid'],
                self.val['inputcollid']
            )

    def children(self):
        list = []
        if rtes.rtes == None:
            add_list(list, self.val, 'args')
        return list

def format_type_extended(type, mod):

    return 'None'

@register_printer('RelabelType')
class RelabelTypePrinter(Printer):
    def to_string(self):
        if gdb.parameter('pg_verbose') == False:
            return '(%s)::%s' % (
                self.val['arg'].dereference(),
                pg_type.get_type(int(self.val['resulttype']))
            )
        else:
            return 'RelabelType[resulttype: %s, resulttypmod: %s, resultcollid: %s, relabelformat: %s]' % (
                self.val['resulttype'],
                self.val['resulttypmod'],
                self.val['resultcollid'],
                self.val['relabelformat']
            )

    def children(self):
        list = []
        if gdb.parameter('pg_verbose') == True:
            add_list(list, self.val, 'arg')
        return list

def is_none(node):
    return str(node) == '0x0'

def list_nth(list, index, type):
    return list['elements'][index][type + '_value']

def get_rte_attribute_name(rte, index):
    if index == 0:
        return '*'

    if str(rte['alias']) != '0x0' and str(rte['alias']['colnames']) != '0x0' and index > 0 and index < int(cast(rte['alias']['colnames'], 'List')['length']):
        return cast(list_nth(cast(rte['alias']['colnames'], 'List'), index - 1, 'ptr'), 'Node').dereference()

    if index > 0 and index <= int(cast(rte['eref']['colnames'], 'List')['length']):
        return cast(list_nth(cast(rte['eref']['colnames'], 'List'), index - 1, 'ptr'), 'Node').dereference()
    return 'None'

@register_printer('Var')
class VarPrinter(Printer):
    def to_string(self):
        if rtes.rtes != None:
            if int(self.val['varno']) == -1:
                return 'INNER.?'
            elif int(self.val['varno']) == -2:
                return 'OUTER.?'
            elif int(self.val['varno']) == -3:
                return 'INDEX.?'
            elif int(self.val['varno']) == -4:
                return 'ROWID_VAR'
            else:
                node = cast(rtes.get_rte(int(self.val['varno']))['ptr_value'], 'RangeTblEntry')
                return '%s.%s' % (
                    getchars(node['eref']['aliasname'], False),
                    get_rte_attribute_name(node, int(self.val['varattno'])),
                )
        else:
            return self.to_string_pretty('Var', 'varno', 'varattno', 'vartype', 'vartypmod', 'varcollid', 'varlevelsup', 'varnosyn', 'varattnosyn')

    def display_hint(self):
        return 'array'

# TODO add more
def get_const_val(type:int, val:int):
    if type == 16:
        return (True, 'true' if val != 0 else 'false')
    elif type == 20 or type == 21 or type == 23 or type == 26 or type == 28 or type == 29:
        return (True, int(val))
    elif type == 25:
        v = gdb.parse_and_eval('(char*)' + str(val))
        if v[0] == 0x01:
            return (False, 'cant print now')
        elif (v[0] & 0x01) == 0x01:
            len = v[0] >> 1 & 0x7F
            # TODO
            return (True, 'xxx')
        else:
            v = gdb.parse_and_eval('(int32*)' + str(val))
            len = ((v[0] >> 2 ) & 0x3FFFFFFF) - 4
            v = gdb.parse_and_eval('(char*)' + str(val + 4))
            return (True, getchars(v, True, len))

    return (False, '')

@register_printer('Const')
class ConstPrinter(Printer):
    def to_string(self):
        if bool(self.val['constisnull']) == True:
            return 'Null'
        else:
            # TODO: print constant pretty, add more support
            auto = get_const_val(int(self.val['consttype']), int(self.val['constvalue']))
            if auto[0] == True:
                return auto[1]
            else:
                return self.to_string_pretty('Const', 'consttype', 'consttypmod', 'constcollid', 'constlen', 'constvalue', 'constisnull', 'constbyval')

@register_printer('SubPlan')
class SubPlanPrinter(Printer):
    def to_string(self):
        return '[startup_cost: %.2f, per_call_cost: %.2f, subLinkType: %s, plan_id: %s, plan_name: %s, firstColType: %s, firstColTypmod: %s, firstColCollation: %s, useHashTable: %s, unknownEqFalse: %s, parallel_safe: %s]' % (
            float(self.val['startup_cost']),
            float(self.val['per_call_cost']),
            self.val['subLinkType'],
            self.val['plan_id'],
            self.val['plan_name'],
            self.val['firstColType'],
            self.val['firstColTypmod'],
            self.val['firstColCollation'],
            self.val['useHashTable'],
            self.val['unknownEqFalse'],
            self.val['parallel_safe'],
        )

    def children(self):
        return self.children_pretty('testexpr' ,'paramIds' ,'setParam' ,'parParam' ,'args')

@register_printer('Param')
class ParamPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('Param', 'paramkind', 'paramid', 'paramtype', 'paramtypmod', 'paramcollid')

@register_printer('Aggref')
class AggrefPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty( 'aggfnoid' ,'aggtype' ,'aggcollid' ,'inputcollid' ,'aggtranstype' ,'aggstar' ,'aggvariadic' ,'aggkind' ,'agglevelsup' ,'aggsplit')

    def children(self):
        return self.children_pretty('aggargtypes' ,'aggdirectargs' ,'args' ,'aggorder' ,'aggdistinct' ,'aggfilter')

@register_printer('PathTarget')
class PathTargetPrinter(Printer):
    def to_string(self):
        return '[cost: (%.2f..%.2f), width: %s]' % (
            float(self.val['cost']['startup']),
            float(self.val['cost']['per_tuple']),
            self.val['width'],
        )
    def children(self):
        return self.children_pretty('exprs', 'sortgrouprefs')

@register_printer('PlannedStmt')
class PlannedStmtPrinter(Printer):
    def to_string(self):
        return self.to_string_pretty('PlannedStmt', 'commandType', 'queryId', 'hasReturning', 'hasModifyingCTE', 'canSetTag', 'transientPlan', 'dependsOnRole', 'parallelModeNeeded', 'jitFlags')

    def children(self):
        return self.children_pretty('rtable', 'planTree', 'permInfos', 'resultRelations', 'appendRelations', 'subplans', 'rewindPlanIDs', 'rowMarks', 'relationOids', 'invalItems', 'paramExecTypes', 'utilityStmt')


@register_printer('Plan')
class PlanPrinter(Printer):
    def to_string(self):
        type = get_node_type(self.val)
        return self.val.address.cast(gdb.lookup_type(type).pointer()).dereference()

@register_printer('Result')
class ResultPrinter(Printer):
    def to_string(self):
        ext = ''
        return plan_to_string('Result', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'resconstantqual')
        return list

@register_printer('ProjectSet')
class ProjectSetPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ''
        return plan_to_string('ProjectSet', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        return list

@register_printer('ModifyTable')
class ModifyTablePrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <operation: %s, canSetTag: %s, nominalRelation: %s, rootRelation: %s, partColsUpdated: %s, resultRelIndex: %s, rootResultRelIndex: %s, epqParam: %s, onConflictAction: %s, exclRelRTI: %s>' % (
            str(self.val['operation']),
            str(self.val['canSetTag']),
            str(self.val['nominalRelation']),
            str(self.val['rootRelation']),
            str(self.val['partColsUpdated']),
            str(self.val['resultRelIndex']),
            str(self.val['rootResultRelIndex']),
            str(self.val['epqParam']),
            str(self.val['onConflictAction']),
            str(self.val['exclRelRTI']),
        )
        return plan_to_string('ModifyTable', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'resultRelations')
        add_list(list, self.val, 'plans')
        add_list(list, self.val, 'withCheckOptionLists')
        add_list(list, self.val, 'returningLists')
        add_list(list, self.val, 'fdwPrivLists')
        add_list(list, self.val, 'fdwDirectModifyPlans')
        add_list(list, self.val, 'rowMarks')
        add_list(list, self.val, 'arbiterIndexes')
        add_list(list, self.val, 'onConflictSet')
        add_list(list, self.val, 'onConflictWhere')
        add_list(list, self.val, 'exclRelTlist')
        add_list(list, self.val, 'remote_plans')
        add_list(list, self.val, 'resultAttnos')
        add_list(list, self.val, 'param_new')
        add_list(list, self.val, 'param_old')
        return list

@register_printer('Append')
class AppendPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <first_partial_plan: %s>' % str(self.val['first_partial_plan'])
        return plan_to_string('Append', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'apprelids')
        add_list(list, self.val, 'appendplans')
        add_list(list, self.val, 'part_prune_info')
        return list

@register_printer('MergeAppend')
class MergeAppendPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <numCols: %s>' % str(self.val['numCols'])
        return plan_to_string('MergeAppend', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'apprelids')
        add_list(list, self.val, 'mergeplans')
        add_list(list, self.val, 'sortColIdx')
        add_list(list, self.val, 'sortOperators')
        add_list(list, self.val, 'collations')
        add_list(list, self.val, 'nullsFirst')
        add_list(list, self.val, 'part_prune_info')
        return list

@register_printer('RecursiveUnion')
class RecursiveUnionPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <wtParam: %s, numCols: %s, numGroups: %s>' % (
            str(self.val['wtParam']),
            str(self.val['numCols']),
            str(self.val['numGroups'])
        )
        return plan_to_string('RecursiveUnion', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'dupColIdx')
        add_list(list, self.val, 'dupOperators')
        add_list(list, self.val, 'dupCollations')
        return list

@register_printer('BitmapAnd')
class BitmapAndPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ''
        return plan_to_string('BitmapAnd', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'bitmapplans')
        return list

@register_printer('BitmapOr')
class BitmapAndPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <isshared: %s>' % str(self.val['isshared'])
        return plan_to_string('BitmapOr', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'bitmapplans')
        return list

# TODO: scan plan family
@register_printer('SeqScan')
class SeqScanPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ''
        #  TODO select from database?
        if rtes.rtes != None:
            node = cast(rtes.get_rte(int(self.val['scan']['scanrelid']))['ptr_value'], 'RangeTblEntry')
            ext += ' on %s' % getchars(node['eref']['aliasname'], True)
        else:
            ext = ' <scanrelid: %s>' % str(self.val['scan']['scanrelid'])

        return plan_to_string('SeqScan', self.val['scan']['plan']) + ext

    def children(self):
        if rtes.rtes != None:
            return plan_children(self.val['scan']['plan'])
        else:
            return []

@register_printer('SubqueryScan')
class SubqueryScanPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <scanrelid: %s, scanstatus: %s>' % (
            str(self.val['scan']['scanrelid']),
            self.val['scanstatus'],
        )
        return plan_to_string('SubqueryScan', self.val['scan']['plan']) + ext

    def children(self):
        list = []
        add_list(list, self.val, 'subplan')
        return list

@register_printer('RemoteQuery')
class RemoteQueryPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        return '[exec_direct_type: %s, combine_type: %s, read_only: %s, force_autocommit: %s, exec_type: %s, rq_params_internal: %s]' % (
            self.val['exec_direct_type'],
            self.val['combine_type'],
            self.val['read_only'],
            self.val['force_autocommit'],
            self.val['exec_type'],
            self.val['rq_params_internal'],
        )

    def children(self):
        list = []
        list.append(('scan', self.val['scan']))
        add_list(list, self.val, 'exec_nodes')
        add_list(list, self.val, 'reduce_expr')
        add_list(list, self.val, 'remote_query')
        add_list(list, self.val, 'base_tlist')
        add_list(list, self.val, 'coord_var_tlist')
        add_list(list, self.val, 'query_var_tlist')
        return list

# TODO: join plan family
@register_printer('Join')
class JoinPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <jointype: %s, inner_unique: %s>' % (str(self.val['jointype']), str(self.val['inner_unique']))
        return plan_to_string('Join', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'joinqual')
        return list

@register_printer('Material')
class MaterialPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ''
        return plan_to_string('Material', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        return list

@register_printer('Sort')
class SortPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <numCols: %s>' % (
            str(self.val['numCols']),
        )
        return plan_to_string('Sort', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'sortColIdx')
        add_list(list, self.val, 'sortOperators')
        add_list(list, self.val, 'collations')
        add_list(list, self.val, 'nullsFirst')
        return list

@register_printer('Group')
class GroupPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <numCols: %s>' % (
            str(self.val['numCols']),
        )
        return plan_to_string('Group', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'grpColIdx')
        add_list(list, self.val, 'grpOperators')
        add_list(list, self.val, 'grpCollations')
        return list

@register_printer('Agg')
class AggPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <aggstrategy: %s, aggsplit: %s, numCols: %s, numGroups: %s, transitionSpace: %s>' % (
            str(self.val['aggstrategy']),
            str(self.val['aggsplit']),
            str(self.val['numCols']),
            str(self.val['numGroups']),
            str(self.val['transitionSpace']),
        )
        return plan_to_string('Agg', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'grpColIdx')
        add_list(list, self.val, 'grpOperators')
        add_list(list, self.val, 'grpCollations')
        add_list(list, self.val, 'aggParams')
        add_list(list, self.val, 'groupingSets')
        add_list(list, self.val, 'chain')
        return list


@register_printer('Unique')
class UniquePrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <numCols: %s>' % (
            str(self.val['numCols'])
        )
        return plan_to_string('Unique', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'uniqColIdx')
        add_list(list, self.val, 'uniqOperators')
        add_list(list, self.val, 'uniqCollations')
        return list

@register_printer('Gather')
class GatherPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <num_workers: %s, rescan_param: %s, single_copy: %s>' % (
            str(self.val['num_workers']),
            str(self.val['rescan_param']),
            str(self.val['single_copy'])
        )
        return plan_to_string('Gather', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'initParam')
        return list

@register_printer('GatherMerge')
class GatherMergePrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <num_workers: %s, rescan_param: %s, numCols: %s>' % (
            str(self.val['num_workers']),
            str(self.val['rescan_param']),
            str(self.val['numCols'])
        )
        return plan_to_string('GatherMerge', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'sortColIdx')
        add_list(list, self.val, 'sortOperators')
        add_list(list, self.val, 'collations')
        add_list(list, self.val, 'nullsFirst')
        add_list(list, self.val, 'initParam')
        return list

@register_printer('Hash')
class HashPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <skewTable: %s, skewColumn: %s, skewInherit: %s, rows_total: %s>' % (
            str(self.val['skewTable']),
            str(self.val['skewColumn']),
            str(self.val['skewInherit']),
            str(self.val['rows_total'])
        )
        return plan_to_string('Hash', self.val['plan']) + ext

    def children(self):
        return plan_children(self.val['plan'])

@register_printer('SetOp')
class SetOpPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <cmd: %s, strategy: %s, numCols: %s, flagColIdx: %s, firstFlag: %s, numGroups: %s>' % (
            str(self.val['cmd']),
            str(self.val['strategy']),
            str(self.val['numCols']),
            str(self.val['flagColIdx']),
            str(self.val['firstFlag']),
            str(self.val['numGroups'])
        )
        return plan_to_string('SetOp', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'dupColIdx')
        add_list(list, self.val, 'dupOperators')
        add_list(list, self.val, 'dupCollations')
        return list

@register_printer('LockRows')
class LockRowsPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <epqParam: %s>' % (
            str(self.val['epqParam']),
        )
        return plan_to_string('LockRows', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'rowMarks')
        return list

@register_printer('Limit')
class LimitPrinter:
    def __init__(self, val) -> None:
        self.val = val

    def to_string(self):
        ext = ' <limitOption: %s, uniqNumCols: %s>' % (
            str(self.val['limitOption']),
            str(self.val['uniqNumCols']),
        )
        return plan_to_string('Limit', self.val['plan']) + ext

    def children(self):
        list = plan_children(self.val['plan'])
        add_list(list, self.val, 'limitOffset')
        add_list(list, self.val, 'limitCount')
        add_list(list, self.val, 'uniqColIdx')
        add_list(list, self.val, 'uniqOperators')
        add_list(list, self.val, 'uniqCollations')
        return list

gdb.printing.register_pretty_printer(
    gdb.current_objfile(),
    printer, True)

class printVerbose(gdb.Parameter):
    def __init__(self) -> None:
        super(printVerbose, self).__init__('pg_verbose', gdb.COMMAND_DATA, gdb.PARAM_BOOLEAN)
        self.value = False

    def get_set_string(self) -> str:
        return ''



printVerbose()

