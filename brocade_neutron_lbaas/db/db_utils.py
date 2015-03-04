
'''
 Copyright 2013 by Brocade Communication Systems
 All rights reserved.

 This software is the confidential and proprietary information
 of Brocade Communication Systems, ("Confidential Information").
 You shall not disclose such Confidential Information and shall
 use it only in accordance with the terms of the license agreement
 you entered into with Brocade Communication Systems.
'''
# Utility class that the db table uses
from sqlalchemy.sql.expression import or_
def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = getattr(row, column.name)
    return d

def _fields(resource, fields):
    if fields:
        return dict((key, item) for key, item in resource.iteritems()
                    if key in fields)
    return resource

def _model_query(context,model):
    query = context.session.query(model)
    return query

def _get_by_id(context,model, id):
    query = _model_query(context,model)
    return query.filter(model.id == id).one()
    
def _get_resource(context,model, id):
    r = _get_by_id(context,model, id)
    return r
    
def _apply_filters_to_query(query, model,filters,joins=None,orfilters=None):
    if filters:
        for key, value in filters.iteritems():
            column = getattr(model, key, None)
            if column:
                query = query.filter(column.in_([value]))
            elif (joins!=None):
                key_splits=key.split(".")
                for model_j in joins:
                    if(model_j.__name__==key_splits[0]):
                        column = getattr(model_j, key_splits[1], None)
                        if column:
                            query = query.filter(column.in_([value]))
            
    if orfilters:
        _list=[]
        for key, value in orfilters.iteritems():
            column = getattr(model, key, None)
            if column:
                _list.append(column.in_([value]))
                #query = query.filter(or_(column.in_([value])))
            elif (joins!=None):
                key_splits=key.split(".")
                for model_j in joins:
                    if(model_j.__name__==key_splits[0]):
                        column = getattr(model_j, key_splits[1], None)
                        if column:
                            _list.append(column.in_([value]))
                            #query = query.filter(or_(column.in_([value])))  
        query=query.filter(or_(*_list))           
    return query

def _apply_order_by_to_query(query, model, order_by_columns):
    if order_by_columns:
        for key, value in order_by_columns.iteritems():
            column = getattr(model, key, None)
            if column:
                order = str.upper(str(value))
                if 'ASC' in order:
                    query=query.order_by(column.asc())
                else:
                    query = query.order_by(column.desc())
    return query

def _paginate_query(query,limit,offset):
    query = query.limit(limit).offset(offset)
    
    return query

def _get_collection_query(context,model, filters=None, sorts=None, limit=None, offset=0,joins=None,orfilters=None):
    collection = _model_query(context,model)
    collection = _apply_order_by_to_query(collection, model, sorts)
    if(joins!=None):
        collection = _apply_joins_to_query(collection,joins)
    collection = _apply_filters_to_query(collection, model,filters,joins,orfilters)
    if limit!=None:
        collection = _paginate_query(collection,limit,offset)
    
    return collection


def _apply_joins_to_query(collection, joins):
    for model in joins:
        collection = collection.outerjoin(model)
    return collection


def _get_collection(context,model, dict_func, filters=None,
                    fields=None, sorts=None, limit=None, offset=0,joins=None,marker_obj=None,
                    page_reverse=False,orfilters=None):
    query = _get_collection_query(context,model, filters,sorts,limit,offset,joins,orfilters)
    return [dict_func(c, fields) for c in query.all()]

def _get_collection_count(context,model, filters=None):
    return _get_collection_query(context,model, filters).count()
    