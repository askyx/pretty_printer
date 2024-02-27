import gdb
import string
import re
import os
import sys

current_file_path = os.path.abspath(__file__)

current_dir = os.path.dirname(current_file_path)

if current_dir not in sys.path:
    sys.path.append(current_dir)

from node_struct import *

printer = gdb.printing.RegexpCollectionPrettyPrinter("PostgreSQL 16beta2")

def register_printer(name):
    def __registe(_printer):
        printer.add_printer(name, '^' + name + '$', _printer)
    return __registe

def getTypeOutputInfo(t_oid):
    tupe = gdb.parse_and_eval('SearchSysCache1(TYPEOID, {})'.format(t_oid))
    tp = gdb.parse_and_eval('(Form_pg_type){}'.format(int(tupe['t_data']) + int(tupe['t_data']['t_hoff'])))
    gdb.parse_and_eval('ReleaseSysCache({})'.format(tupe.dereference().address))
    return [int(tp['typoutput']), (not bool(tp['typbyval'])) and int(tp['typlen']) == -1]

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

@register_printer('Node')
class NodePrinter(Printer):
    def to_string(self):
        type = get_node_type(self.val)
        if type == 'A_Star':
            return '*'
        return self.val.address.cast(gdb.lookup_type(type).pointer()).dereference()

@register_printer('Bitmapset')
class BitmapsetPrinter(Printer):
    def to_string(self):
        list = []
        index = int(gdb.parse_and_eval('bms_next_member({}, {})'.format(self.val.reference_value().address, -1)))
        while index >= 0:
            list.append(index)
            index = int(gdb.parse_and_eval('bms_next_member({}, {})'.format(self.val.reference_value().address, index)))

        return str(list)

@register_printer('Relids')
class RelidsPrinter(Printer):
    def to_string(self):
        return self.val.address.cast(gdb.lookup_type('Bitmapset').pointer()).dereference()


pl = {
    'Alias': Alias,         'RangeVar': RangeVar,
    'TableFunc': TableFunc, 'IntoClause': IntoClause,
    'Var': Var,
    'Const': Const,
    'Param': Param,
    'Aggref': Aggref,
    'GroupingFunc': GroupingFunc,
    'WindowFunc': WindowFunc,
    'SubscriptingRef': SubscriptingRef,
    'FuncExpr': FuncExpr,
    'NamedArgExpr': NamedArgExpr,
    'OpExpr': OpExpr,
    'DistinctExpr': DistinctExpr,
    'NullIfExpr': NullIfExpr,
    'ScalarArrayOpExpr': ScalarArrayOpExpr,
    'BoolExpr': BoolExpr,
    'SubLink': SubLink,
    'SubPlan': SubPlan,
    'AlternativeSubPlan': AlternativeSubPlan,
    'FieldSelect': FieldSelect,
    'FieldStore': FieldStore,
    'RelabelType': RelabelType,
    'CoerceViaIO': CoerceViaIO,
    'ArrayCoerceExpr': ArrayCoerceExpr,
    'ConvertRowtypeExpr': ConvertRowtypeExpr,
    'CollateExpr': CollateExpr,
    'CaseExpr': CaseExpr,
    'CaseWhen': CaseWhen,
    'CaseTestExpr': CaseTestExpr,
    'ArrayExpr': ArrayExpr,
    'RowExpr': RowExpr,
    'RowCompareExpr': RowCompareExpr,
    'CoalesceExpr': CoalesceExpr,
    'MinMaxExpr': MinMaxExpr,
    'SQLValueFunction': SQLValueFunction,
    'XmlExpr': XmlExpr,
    'JsonFormat': JsonFormat,
    'JsonReturning': JsonReturning,
    'JsonValueExpr': JsonValueExpr,
    'JsonConstructorExpr': JsonConstructorExpr,
    'JsonIsPredicate': JsonIsPredicate,
    'NullTest': NullTest,
    'BooleanTest': BooleanTest,
    'CoerceToDomain': CoerceToDomain,
    'CoerceToDomainValue': CoerceToDomainValue,
    'SetToDefault': SetToDefault,
    'CurrentOfExpr': CurrentOfExpr,
    'NextValueExpr': NextValueExpr,
    'InferenceElem': InferenceElem,
    'TargetEntry': TargetEntry,
    'RangeTblRef': RangeTblRef,
    'JoinExpr': JoinExpr,
    'FromExpr': FromExpr,
    'OnConflictExpr': OnConflictExpr,
    'Query': Query,
    'TypeName': TypeName,
    'ColumnRef': ColumnRef,
    'ParamRef': ParamRef,
    'A_Expr': A_Expr,
    'A_Const': A_Const,
    'TypeCast': TypeCast,
    'CollateClause': CollateClause,
    'RoleSpec': RoleSpec,
    'FuncCall': FuncCall,
    'A_Star': A_Star,
    'A_Indices': A_Indices,
    'A_Indirection': A_Indirection,
    'A_ArrayExpr': A_ArrayExpr,
    'ResTarget': ResTarget,
    'MultiAssignRef': MultiAssignRef,
    'SortBy': SortBy,
    'WindowDef': WindowDef,
    'RangeSubselect': RangeSubselect,
    'RangeFunction': RangeFunction,
    'RangeTableFunc': RangeTableFunc,
    'RangeTableFuncCol': RangeTableFuncCol,
    'RangeTableSample': RangeTableSample,
    'ColumnDef': ColumnDef,
    'TableLikeClause': TableLikeClause,
    'IndexElem': IndexElem,
    'DefElem': DefElem,
    'LockingClause': LockingClause,
    'XmlSerialize': XmlSerialize,
    'PartitionElem': PartitionElem,
    'PartitionSpec': PartitionSpec,
    'PartitionBoundSpec': PartitionBoundSpec,
    'PartitionRangeDatum': PartitionRangeDatum,
    'PartitionCmd': PartitionCmd,
    'RangeTblEntry': RangeTblEntry,
    'RTEPermissionInfo': RTEPermissionInfo,
    'RangeTblFunction': RangeTblFunction,
    'TableSampleClause': TableSampleClause,
    'WithCheckOption': WithCheckOption,
    'SortGroupClause': SortGroupClause,
    'GroupingSet': GroupingSet,
    'WindowClause': WindowClause,
    'RowMarkClause': RowMarkClause,
    'WithClause': WithClause,
    'InferClause': InferClause,
    'OnConflictClause': OnConflictClause,
    'CTESearchClause': CTESearchClause,
    'CTECycleClause': CTECycleClause,
    'CommonTableExpr': CommonTableExpr,
    'MergeWhenClause': MergeWhenClause,
    'MergeAction': MergeAction,
    'TriggerTransition': TriggerTransition,
    'JsonOutput': JsonOutput,
    'JsonKeyValue': JsonKeyValue,
    'JsonObjectConstructor': JsonObjectConstructor,
    'JsonArrayConstructor': JsonArrayConstructor,
    'JsonArrayQueryConstructor': JsonArrayQueryConstructor,
    'JsonAggConstructor': JsonAggConstructor,
    'JsonObjectAgg': JsonObjectAgg,
    'JsonArrayAgg': JsonArrayAgg,
    'RawStmt': RawStmt,
    'InsertStmt': InsertStmt,
    'DeleteStmt': DeleteStmt,
    'UpdateStmt': UpdateStmt,
    'MergeStmt': MergeStmt,
    'SelectStmt': SelectStmt,
    'SetOperationStmt': SetOperationStmt,
    'ReturnStmt': ReturnStmt,
    'PLAssignStmt': PLAssignStmt,
    'CreateSchemaStmt': CreateSchemaStmt,
    'AlterTableStmt': AlterTableStmt,
    'ReplicaIdentityStmt': ReplicaIdentityStmt,
    'AlterTableCmd': AlterTableCmd,
    'AlterCollationStmt': AlterCollationStmt,
    'AlterDomainStmt': AlterDomainStmt,
    'GrantStmt': GrantStmt,
    'ObjectWithArgs': ObjectWithArgs,
    'AccessPriv': AccessPriv,
    'GrantRoleStmt': GrantRoleStmt,
    'AlterDefaultPrivilegesStmt': AlterDefaultPrivilegesStmt,
    'CopyStmt': CopyStmt,
    'VariableSetStmt': VariableSetStmt,
    'VariableShowStmt': VariableShowStmt,
    'CreateStmt': CreateStmt,
    'Constraint': Constraint,
    'CreateTableSpaceStmt': CreateTableSpaceStmt,
    'DropTableSpaceStmt': DropTableSpaceStmt,
    'AlterTableSpaceOptionsStmt': AlterTableSpaceOptionsStmt,
    'AlterTableMoveAllStmt': AlterTableMoveAllStmt,
    'CreateExtensionStmt': CreateExtensionStmt,
    'AlterExtensionStmt': AlterExtensionStmt,
    'AlterExtensionContentsStmt': AlterExtensionContentsStmt,
    'CreateFdwStmt': CreateFdwStmt,
    'AlterFdwStmt': AlterFdwStmt,
    'CreateForeignServerStmt': CreateForeignServerStmt,
    'AlterForeignServerStmt': AlterForeignServerStmt,
    'CreateForeignTableStmt': CreateForeignTableStmt,
    'CreateUserMappingStmt': CreateUserMappingStmt,
    'AlterUserMappingStmt': AlterUserMappingStmt,
    'DropUserMappingStmt': DropUserMappingStmt,
    'ImportForeignSchemaStmt': ImportForeignSchemaStmt,
    'CreatePolicyStmt': CreatePolicyStmt,
    'AlterPolicyStmt': AlterPolicyStmt,
    'CreateAmStmt': CreateAmStmt,
    'CreateTrigStmt': CreateTrigStmt,
    'CreateEventTrigStmt': CreateEventTrigStmt,
    'AlterEventTrigStmt': AlterEventTrigStmt,
    'CreatePLangStmt': CreatePLangStmt,
    'CreateRoleStmt': CreateRoleStmt,
    'AlterRoleStmt': AlterRoleStmt,
    'AlterRoleSetStmt': AlterRoleSetStmt,
    'DropRoleStmt': DropRoleStmt,
    'CreateSeqStmt': CreateSeqStmt,
    'AlterSeqStmt': AlterSeqStmt,
    'DefineStmt': DefineStmt,
    'CreateDomainStmt': CreateDomainStmt,
    'CreateOpClassStmt': CreateOpClassStmt,
    'CreateOpClassItem': CreateOpClassItem,
    'CreateOpFamilyStmt': CreateOpFamilyStmt,
    'AlterOpFamilyStmt': AlterOpFamilyStmt,
    'DropStmt': DropStmt,
    'TruncateStmt': TruncateStmt,
    'CommentStmt': CommentStmt,
    'SecLabelStmt': SecLabelStmt,
    'DeclareCursorStmt': DeclareCursorStmt,
    'ClosePortalStmt': ClosePortalStmt,
    'FetchStmt': FetchStmt,
    'IndexStmt': IndexStmt,
    'CreateStatsStmt': CreateStatsStmt,
    'StatsElem': StatsElem,
    'AlterStatsStmt': AlterStatsStmt,
    'CreateFunctionStmt': CreateFunctionStmt,
    'FunctionParameter': FunctionParameter,
    'AlterFunctionStmt': AlterFunctionStmt,
    'DoStmt': DoStmt,
    'CallStmt': CallStmt,
    'RenameStmt': RenameStmt,
    'AlterObjectDependsStmt': AlterObjectDependsStmt,
    'AlterObjectSchemaStmt': AlterObjectSchemaStmt,
    'AlterOwnerStmt': AlterOwnerStmt,
    'AlterOperatorStmt': AlterOperatorStmt,
    'AlterTypeStmt': AlterTypeStmt,
    'RuleStmt': RuleStmt,
    'NotifyStmt': NotifyStmt,
    'ListenStmt': ListenStmt,
    'UnlistenStmt': UnlistenStmt,
    'TransactionStmt': TransactionStmt,
    'CompositeTypeStmt': CompositeTypeStmt,
    'CreateEnumStmt': CreateEnumStmt,
    'CreateRangeStmt': CreateRangeStmt,
    'AlterEnumStmt': AlterEnumStmt,
    'ViewStmt': ViewStmt,
    'LoadStmt': LoadStmt,
    'CreatedbStmt': CreatedbStmt,
    'AlterDatabaseStmt': AlterDatabaseStmt,
    'AlterDatabaseRefreshCollStmt': AlterDatabaseRefreshCollStmt,
    'AlterDatabaseSetStmt': AlterDatabaseSetStmt,
    'DropdbStmt': DropdbStmt,
    'AlterSystemStmt': AlterSystemStmt,
    'ClusterStmt': ClusterStmt,
    'VacuumStmt': VacuumStmt,
    'VacuumRelation': VacuumRelation,
    'ExplainStmt': ExplainStmt,
    'CreateTableAsStmt': CreateTableAsStmt,
    'RefreshMatViewStmt': RefreshMatViewStmt,
    'CheckPointStmt': CheckPointStmt,
    'DiscardStmt': DiscardStmt,
    'LockStmt': LockStmt,
    'ConstraintsSetStmt': ConstraintsSetStmt,
    'ReindexStmt': ReindexStmt,
    'CreateConversionStmt': CreateConversionStmt,
    'CreateCastStmt': CreateCastStmt,
    'CreateTransformStmt': CreateTransformStmt,
    'PrepareStmt': PrepareStmt,
    'ExecuteStmt': ExecuteStmt,
    'DeallocateStmt': DeallocateStmt,
    'DropOwnedStmt': DropOwnedStmt,
    'ReassignOwnedStmt': ReassignOwnedStmt,
    'AlterTSDictionaryStmt': AlterTSDictionaryStmt,
    'AlterTSConfigurationStmt': AlterTSConfigurationStmt,
    'PublicationTable': PublicationTable,
    'PublicationObjSpec': PublicationObjSpec,
    'CreatePublicationStmt': CreatePublicationStmt,
    'AlterPublicationStmt': AlterPublicationStmt,
    'CreateSubscriptionStmt': CreateSubscriptionStmt,
    'AlterSubscriptionStmt': AlterSubscriptionStmt,
    'DropSubscriptionStmt': DropSubscriptionStmt,
    'PlannerGlobal': PlannerGlobal,
    'PlannerInfo': PlannerInfo,
    'RelOptInfo': RelOptInfo,
    'IndexOptInfo': IndexOptInfo,
    'ForeignKeyOptInfo': ForeignKeyOptInfo,
    'StatisticExtInfo': StatisticExtInfo,
    'JoinDomain': JoinDomain,
    'EquivalenceClass': EquivalenceClass,
    'EquivalenceMember': EquivalenceMember,
    'PathKey': PathKey,
    'PathTarget': PathTarget,
    'ParamPathInfo': ParamPathInfo,
    'RestrictInfo': RestrictInfo,
    'PlaceHolderVar': PlaceHolderVar,
    'SpecialJoinInfo': SpecialJoinInfo,
    'OuterJoinClauseInfo': OuterJoinClauseInfo,
    'AppendRelInfo': AppendRelInfo,
    'RowIdentityVarInfo': RowIdentityVarInfo,
    'PlaceHolderInfo': PlaceHolderInfo,
    'MinMaxAggInfo': MinMaxAggInfo,
    'PlannerParamItem': PlannerParamItem,
    'AggInfo': AggInfo,
    'AggTransInfo': AggTransInfo,
    'PlannedStmt': PlannedStmt,
    'PlanRowMark': PlanRowMark,
    'PartitionPruneInfo': PartitionPruneInfo,
    'PartitionedRelPruneInfo': PartitionedRelPruneInfo,
    'PartitionPruneStep': PartitionPruneStep,
    'PartitionPruneStepOp': PartitionPruneStepOp,
    'PartitionPruneStepCombine': PartitionPruneStepCombine,
    'PlanInvalItem': PlanInvalItem,
    'ExtensibleNode': ExtensibleNode,
    'ForeignKeyCacheInfo': ForeignKeyCacheInfo,
}

def gen_printer_class(class_name, fields):
    class Printer():
        def __init__(self, val) -> None:
            self.val = val

        def to_string(self):
            pod = fields[0]
            size = len(pod)
            ret = '%s ' % class_name
            if size > 1:
                ret += '{'

            ss = []
            for arg in pod:
                s = '%s: %s' % (arg[1], getchars(self.val[arg[1]]) if arg[0] == 'char*' else self.val[arg[1]])
                ss.append(s)

            ret += ', '.join(ss)

            if size > 1:
                ret += '}'

            return ret

        def children(self):
            list = []
            for arg in fields[1]:
                add_list(list, self.val, arg[1])
            return list

        def display_hint(self):
            return ''

    Printer.__name__ = class_name
    return Printer

def split_field(s):
    pod_item = []
    pointer_item = []
    for key, val in s:
        if re.search('\*', key) and key != 'char*':
            pointer_item.append([key, val])
        else:
            pod_item.append([key, val])

    return [pod_item, pointer_item]

def generate_printer():
    for name, s in pl.items():
        pointerx = gen_printer_class(name, split_field(s))
        printer.add_printer(name, '^' + name + '$', pointerx)

generate_printer()

def get_node_type(node):
    type = str(node['type'])[2:]
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
    add_list(list, plan, 'targetlist')
    add_list(list, plan, 'qual')
    add_list(list, plan, 'initPlan')
    add_list(list, plan, 'lefttree')
    add_list(list, plan, 'righttree')
    add_list(list, plan, 'extParam')
    add_list(list, plan, 'allParam')
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

def list_length(node):
    return int(cast(node, 'List')['length'])

# @register_printer('OpExpr')
# class OpExprPrinter(Printer):
#     def to_string(self):
#         opname = gdb.parse_and_eval('get_opname({})'.format(self.val['opno']))
#         if str(opname) == '0x0':
#             opname = '(invalid operator)'
#         if list_length(self.val['args']) > 1:
#             lop = list_nth_node(self.val['args'], 0).dereference()
#             rop = list_nth_node(self.val['args'], 1).dereference()
#             return '%s %s %s' % (lop, opname, rop)
#         else:
#             op = list_nth_node(self.val['args'], 0).dereference()
#             return '%s %s' % (op, opname)

def is_none(node):
    return str(node) == '0x0'

def list_nth(list, index, type):
    l = cast(list, 'List')
    return l['elements'][index][type + '_value']

def list_nth_node(list, index):
    return cast(list_nth(list, index, 'ptr'), 'Node')

# @register_printer('Const')
# class ConstPrinter(Printer):
#     def to_string(self):
#         if bool(self.val['constisnull']) == True:
#             return 'Null'
#         else:
#             pfunc = getTypeOutputInfo(int(self.val['consttype']))
#             return str(gdb.parse_and_eval('OidOutputFunctionCall({}, {})'.format(pfunc[0], int(self.val['constvalue']))).dereference())


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
        ext = ' <scanrelid: %s>' % str(self.val['scan']['scanrelid'])
        return plan_to_string('SeqScan', self.val['scan']['plan']) + ext

    def children(self):
        return plan_children(self.val['scan']['plan'])

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
        super(printVerbose, self).__init__('print pg_pretty', gdb.COMMAND_DATA, gdb.PARAM_BOOLEAN)
        self.value = True

    def get_set_string(self) -> str:
        if self.value == False:
            for p in printer.subprinters:
                p.enabled = False
        else:
            for p in printer.subprinters:
                p.enabled = True

    def get_show_string(self, pvalue):
        if self.value == True:
           return "Current value is 'True', you can 'set print level'  "
        else:
           return "Current value is 'False'"

class printerTurn(gdb.Parameter):
    def __init__(self) -> None:
        super(printerTurn, self).__init__('print level', gdb.COMMAND_DATA, gdb.PARAM_ENUM, ['trace', 'info'])
        self.enum = ['trace', 'info']
        self.value = self.enum[0]


printerTurn()
printVerbose()
