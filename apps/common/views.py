from django.db.models.query import QOr

from django.core.paginator import ObjectPaginator
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.forms import FormWrapper

from serpantin.settings import user

def async_listform(request, app_name, model_name, node):
#FIXME: commented checking on anonymous
#  if not request.user.is_anonymous():
    #model = meta.get_module(app_name, model_name)
    print "RA3VAT app_name ", app_name
    print "RA3VAT model_name ", model_name
    model = getattr(__import__('serpantin.apps.%s.models' % (app_name), '', '', [model_name]), model_name)
    print "RA3VAT model ", model
    #obj_list = model.get_list(order_by=(['-createdate']))
    obj_list = []
    paginator = None
    if 1:
#    try:
        paginate_by = 10
        q = request.GET.get('q','')
        #FIXME: order_by does not work
        #prop ={'order_by': ['-createdate']}
        prop = {}
        ql = []
        
        if q:
            try:
                #flds = model._meta.admin.list_display
                flds = tuple(model._meta.admin.search_fields)
            except:
                flds = tuple()
            #	print "Fields ", flds[1:]	  
            #	key = '%s__icontains' % flds[0]
            #	kwargs = {key:q} 
            print "RA3VAT flds ", flds
            for f in flds:
                if not  model._meta.get_field(f).get_internal_type() in ['ForeignKey','LookupField']:
                    ql.append(Q(**{'%s__icontains' % f:q}))
                else:
                    for fkf in tuple(model._meta.get_field(f).rel.to._meta.admin.search_fields):
                        kw = {'%s__%s__icontains' % (f, fkf):q}
                        ql.append(Q(**kw))
        print "RA3VAT ql ", ql
        ResQ = QOr(*ql)
        print "RA3VAT ResQ ", ResQ
        #if model._meta.__dict__.has_key('ordering'):
        try:
            order_field = model._meta.ordering[0]
        except:
            order_field = '-modifydate'
	print "RA3VAT before queryset"
        queryset = model.objects.filter(ResQ).order_by(order_field)
        paginator = ObjectPaginator(queryset, 10)
        page = int(request.GET.get('page',0))
	#page = 0
	print "before obj_list"
        try:
            obj_list = paginator.get_page(page)
        except:		
            print "obj_list ", obj_list
#    except:
#        raise Http404
    
    params = {
        'is_paginated': paginator.pages > 1,
        'results_per_page': paginate_by,
        'has_next': paginator.has_next_page(page),
        'has_previous': paginator.has_previous_page(page),
        'page': page + 1,
        'next': page + 1,
        'previous': page - 1,
        'pages': paginator.pages,
        'hits' : paginator.hits,
        'is_owner': True,
        'obj_list': obj_list,
        'app': app_name,
        'model': model_name,
        'node': node,
    }
   
    print "before render_to_response"
   
    #if 1:
    try:
        tmpl = '%s/apps/%s/templates/%s_list.html' % (user['projectdir'], app_name, model_name) 
        return render_to_response(tmpl, params, context_instance=RequestContext(request))
    except:
        tmpl = '%s/apps/%s/templates/%s_list.gen.html' % (user['projectdir'], app_name, model_name) 
        print "before render_to_response final"
	
        return render_to_response(tmpl, params, context_instance=RequestContext(request))



def async_form(request, app_name, model_name, win_id=0, object_id='', async=True, go=False):
    print "RA3VAT async_form"
    print "app_name ", app_name
    print "model_name", model_name
    print "object_id ", object_id
    print "win_id ", win_id
    print "go ", go
    print "request ", request
    boundobj = None

    if request.user.is_anonymous():
        Http404
    else:
        model = getattr(__import__('serpantin.apps.%s.models' % (app_name), '', '', [model_name]), model_name)
        bound_data = {}
        bound_repr = {}
        #try:
	if 1:
            if request.GET and request.GET.has_key('type') and request.GET['type']=='boundform':
                print "RA3VAT managing bound fields "
                bound_fields = model.bound_fields
                for bf in bound_fields:
                    bound_data[bf] = request.GET['oid']
                    boundmodel = getattr(__import__('serp2.apps.%s.models' % (request.GET['app']), '', '', [request.GET['model']]), request.GET['model'])
                    boundobj = boundmodel.objects.get(pk=request.GET['oid'])
                    bound_repr[bf] = boundobj.__str__()
        #except:
        #    pass
                                                                                              
        if object_id:
            obj = model.objects.get(pk=object_id)
            bound = model.__dict__.has_key('bound_fields')
            if bound:
                bound_fields = model.bound_fields
                for bf in bound_fields:
    	            model._meta.get_field(bf).editable=False
            	    boundobj = getattr(obj, bf)
            	    bound_repr[bf] = boundobj.__str__()

            if model_name=='OrgAddress':
                manipulator = OrgAddressChangeManipulator(obj.id)
            elif model_name=='Employee':
                manipulator = EmployeeChangeManipulator(obj.id)
            else:
                manipulator = model.ChangeManipulator(obj.id)
        else:
            obj=''
            if model_name=='OrgAddress':
                manipulator = OrgAddressAddManipulator()
            elif model_name=='PersonAddress':
                manipulator = PersonAddressAddManipulator()
            elif model_name=='Employee':
                manipulator = EmployeeAddManipulator()
            elif model_name=='Client':
                manipulator = ClientAddManipulator()
            elif model_name=='ItemReceipt':
                manipulator = ItemReceiptAddManipulator()
            elif model_name=='TaskLog':
                manipulator = TaskLogAddManipulator()
            else:
                manipulator = model.AddManipulator()
            
        if request.POST:
            print "RA3VAT about to manage POST request..."
            new_data = request.POST.copy()
            print "RA3VAT obj ", obj
            #if new_data['web'] and not new_data['web'].startswith('http://'):
            #    new_data['web']='http://' + new_data['web']

            #try:
            #    obj = model.objects.get(pk=object_id)
            #except:
            #    obj = None
            if obj and obj.createuser:
                print "greg, If createuser has in db ", obj.createuser
                new_data['createuser'] = obj.createuser.id
                new_data['modifyuser'] = str(request.user.id)
                new_obj = False

            else:
                #print "greg, If modifyuser has in db "
                print "Saving new object... "
                new_obj = True
                new_data['createuser'] = str(request.user.id)
                new_data['modifyuser'] = str(request.user.id)

            #Temporary commented out
            #errors = manipulator.get_validation_errors(new_data)
            errors = {}
            if not errors:
                manipulator.do_html2python(new_data)
                #try:
                #if 1:
                print "RA3VAT: about to save...", new_data
                obj = manipulator.save(new_data)
                print "RA3VAT: saved?"
                #except e:
                    #print "RA3VAT save failed ", e
                    #content =  "{\"oper\":\"ERROR error\"}"  
                    #response = HttpResponse(content=content, mimetype="text/plain")
                    #return response
                
            	print "Manipulator saved what?: ", obj.__str__()
                #if async and not go:
                if async:
                    if new_obj:
                        #content =  "{\"oper\":\"ADDED\",\"id\":%d,\"repr\":\"%s\"}" % (obj.id, obj.__str__())
                        content =  {
			    "oper":"ADDED",
			    "id":int(obj.id),
			    "repr":"%s" % obj.__str__()
			}
                        #response = HttpResponse(content=content, mimetype="text/plain")
                        response = JsonResponse(content)
                    else:
                        #print "RA3VAT: CONTENT_TYPE ", response.META['CONTENT_TYPE']
#                        if not request.META['CONTENT_TYPE']=='text/plain':
#                            print "RA3VAT: File submitted.. "
#                            response = HttpResponse(content="<html><head></head><body><h1>IO success</h1></body></html>", mimetype="text/plain")
#                        else:
                        print "RA3VAT: Update operation..."
                        response = HttpResponse(content="{\"oper\":\"UPDATE\"}", mimetype="text/plain")
                    return response	  
            
        else:
            errors = {}
            print errors
            #try:
                #new_data = obj.__dict__
            new_data = manipulator.flatten_data()
            #except:
            #if not new_data:
            #    new_data = {}
            if bound_data:
                new_data = bound_data
                print "RA3VAT new_data for bound ", new_data
            #Check for autonums
            autonum = model.__dict__.has_key('preset_number')
            if not object_id and autonum:
                #new_data['num'] = model.suggestNum()
                new_data['num'] = suggestNum(model)
#                num = 0
#                from serp2.apps.docs.models import Doctype
#                doctype = Doctype.objects.get(classname='%s_%s' % (app_name, model_name),isactive=True)
#                if doctype:
#                    print "RA3VAT doctype=", doctype
#                    try:
#                        doctype.serial = doctype.serial + 1
#                        doctype.save()
#                        #FIXME: get fieldname from preset_number param
#                        new_data['num'] = doctype.serial
#                    except:
#                        pass
                
            has_initial = model.__dict__.has_key('initial_data')
            if has_initial and not obj:
                for name in model.initial_data.keys():
                    new_data[name] = model.initial_data[name]

            has_fill_form = model.__dict__.has_key('fillForm')
            if has_fill_form and not obj:
                model.fillForm(new_data)
  
    
        print "RA3VAT new_data ", new_data	
        form = FormWrapper(manipulator, new_data, errors)
        print "RA3VAT form ", form
        bound_params = ""
        if obj:
            bound = obj.__dict__.has_key('bound_fields')
            if bound:
                for b in obj.bound_fields:
                    bound_params = bound_params + "%s:{{%s}}" % (b,b)
                    bound_params = "{ " + bound_params + " }"
#for f in [elem for elem in mod._meta.admin.list_display if bound and elem not in mod.bound_
#fields or not bound]:
#form += '<th>%s</th>\n' % f
									          
        params = {
            'form': form,
            'edit_object': False,
            'is_owner': True,
            'win_id': win_id,
            'app': app_name,
            'model': model_name,
            'obj': obj,
            'bound': bound_repr,
            'boundobj': boundobj
        }
	
        #try:
    	tmpl = '%s/apps/%s/templates/%s_form.html' % (user['projectdir'], app_name, model_name) 
        return render_to_response(tmpl, params, context_instance=RequestContext(request))
        #except:
        #    tmpl = '%s/apps/%s/templates/%s_form.gen.html' % (user['projectdir'], app_name, model_name) 
        #    return render_to_response(tmpl, params, context_instance=RequestContext(request))
