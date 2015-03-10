<%
from lxml import etree
%>\
<?xml version="1.0" encoding="utf-8"?>
<%def name="missing(fieldname, type, db, model, ids)">
  <%
      str_ids = ", ".join([str(i) for i in ids])
      msg("    ! Missing xmlid for field %r (%s to %s) for those ids: %s"
          % (fieldname, type, model, str_ids))
  %>
  <!-- MISSING xml_id for field ${fieldname} (${type} to ${model}) for those ids: ${str_ids} (db: ${db_identifier}) -->
</%def>
<record id="${xml_id}" model="${model}">
  % for f, fdef in fields:
    % if 'function' not in fdef:
      % if fdef['ttype'] in ["many2one", "one2one"]:
         <%
           value = getattr(r, f)
         %>\
         % if value is not False and value is not None:
           <%
             m, res_id = fdef['relation'], value._ref
             _xml_id = xml_id_mgr.lookup(m, res_id)
             if _xml_id:
                 ref = "%s.%s" % _xml_id
                 deps.append(_xml_id)
           %>
           % if _xml_id is not None:
             <field name=${repr(f)} ref=${repr(ref)} />
           % else:
              ${missing(f, fdef['ttype'], db_identifier, m, [res_id])}
           % endif
         % endif
         <%
           continue
         %>\
      % elif fdef['ttype'] in ['many2many', 'one2many']:
         % if fdef['ttype'] == "one2many":
            <!-- one2many field ${repr(f)} managed on the ${fdef['relation']} side -->
            <% continue %>
         % endif
         <%
           value = getattr(r, f)
         %>\
         % if value is None:
            <% pass %>
         % else:
           <%
             xml_ids = [(v._ref, xml_id_mgr.lookup(value.model, v._ref))
                        for v in value]
             xml_ids = [(id, None if _xml_id is None else ("%s.%s" % _xml_id))
                            for id, _xml_id in xml_ids]
             tuple_list = [("(4, ref(%r))" % x)
                           for _,x in xml_ids if x is not None]
             for _, x in xml_ids:
                 if x is not None:
                     deps.append(x)
            %>
             % if len(tuple_list) > 0:
               <%
                  eval_field = "[%s]" % (", ".join(tuple_list))
                %>
                <field name=${repr(f)} eval=${_pa(eval_field)} />
             % endif
             <%
             anonymous_ids = [str(id) for id, x in xml_ids if x is None]
             %>
             % if len(anonymous_ids) > 0:
                ${missing(f, fdef['ttype'], value.model, db_identifier, anonymous_ids)}
             % endif
         % endif
         <%
             continue
         %>\
      % endif
      <%
          value = getattr(r, f)
          value = value.decode("utf-8") if not isinstance(value, unicode) and isinstance(value, basestring) else value
      %>\


      % if fdef['ttype'] == 'reference':
         % if not value:
            <% pass %>
         % else:
           <%
             m, res_id = value.split(',', 1)
             ref_xml_id = xml_id_mgr.lookup(m, res_id)
             if ref_xml_id:
                 reference_eval = "'%s,' + str(ref(%r))" \
                                  % (m, "%s.%s" % ref_xml_id)
                 deps.append(ref_xml_id)
           %>
           % if ref_xml_id is None:
             ${missing(f, fdef['ttype'], db_identifier, m, [res_id])}
           % else:
          <field name=${repr(f)} eval=${_pa(reference_eval)} />
           % endif
         % endif
      % elif fdef['ttype'] == 'boolean':
          <field name=${repr(f)} eval="${repr(value)}" />
      % elif fdef['ttype'] != 'boolean' and value is False:
        <% pass %>
      % elif not isinstance(value, basestring):
          <field name=${repr(f)}>${value}</field>
      % elif isinstance(value, basestring) and all(c not in getattr(r, f) for c in '<>&'):
          <field name=${repr(f)}>${value.decode("utf-8") if not isinstance(value, unicode) else value}</field>
      % elif f == "arch":
          <%
             try:
                 normalize = etree.tostring(etree.fromstring(value), xml_declaration=False)
             except:
                 normalize = False
          %>
          % if normalize:
          <field name="arch" type="xml">${normalize}</field>
          % else:
          <field name=${repr(f)}><![CDATA[${value}]]></field>
          % endif
      % else:
          <field name=${repr(f)}>${_pv(value)}</field>
      % endif
    % endif
  % endfor
</record>
