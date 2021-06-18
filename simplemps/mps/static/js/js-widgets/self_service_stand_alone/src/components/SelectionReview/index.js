import React, { useContext, useState, useEffect, useRef } from 'react';

import { Table, Input, Button, Popconfirm, Form, Select, message } from 'antd';
import { isNil, forEachObjIndexed, forEach, keys, length, isEmpty, path, compose, omit, assoc} from 'ramda';
import AppContext from '../../store/provider';
import 'antd/dist/antd.css';

const EditableContext = React.createContext(null);
const { Option } = Select;

const EditableRow = ({ index, ...props }) => {
    const [form] = Form.useForm();
    return (
      <Form form={form} component={false}>
        <EditableContext.Provider value={form}>
          <tr {...props} />
        </EditableContext.Provider>
      </Form>
    );
  };
  
  const EditableCell = ({
    title,
    editable,
    children,
    dataIndex,
    record,
    handleSave,
    ...restProps
  }) => {
    const [editing, setEditing] = useState(false);
    const inputRef = useRef(null);
    const form = useContext(EditableContext);
    const app_context = useContext(AppContext);
    useEffect(() => {

      if (editing) {
        inputRef.current.focus();
      }
    }, [editing]);
  
    const toggleEdit = () => {
      setEditing(!editing);
      form.setFieldsValue({
        [dataIndex]: record[dataIndex],
      });
    };
  
    const save = async () => {
      try {
        const values = await form.validateFields();
        toggleEdit();
        handleSave({ ...record, ...values });
      } catch (errInfo) {
        console.log('Save failed:', errInfo);
      }
    };
    
    function handleChange(value, item) {
        const current_sel = inputRef.current.props.id;
        const { updatePrinterOptions, getDeviceDetails, proposal } = app_context;
        current_sel !== 'device' && updatePrinterOptions(item.key);
        current_sel !== 'manufacturer' && getDeviceDetails(item.key, proposal) 
        save()
    }

    let childNode = children;
  
    if (editable) {
      childNode = editing ? (
        <AppContext.Consumer>
          {
            ({makeOpts, shortOpts}) => (
              <Form.Item
                style={{
                  margin: 0,
                }}
                name={dataIndex}
                rules={[
                  {
                    required: true,
                    message: `${title} is required.`,
                  },
                ]}
              >
                { (dataIndex !== 'manufacturer' && dataIndex !== 'device') ? 
                    <Input ref={inputRef} onPressEnter={save} onBlur={save} /> : 
                    <Select ref={inputRef} style={{ width: 120 }} onChange={handleChange}> 
                        {
                          (dataIndex !== 'device') ?
                            makeOpts.map((item) => (<Option value={item.name} key={item.value}>{item.name}</Option>)) :
                            shortOpts.map((item) => (<Option value={item.name} key={item.value}>{item.name}</Option>))
                        }
                    </Select> 
                }
              </Form.Item>
            )
          }
        </AppContext.Consumer>
        
      ) : (
        <div
          className="editable-cell-value-wrap"
          style={{
            paddingRight: 24,
          }}
          onClick={toggleEdit}
        >
          {children}
        </div>
      );
    }
  
    return <td {...restProps}>{childNode}</td>;
  };
  
  class EditableTable extends React.Component {
    static contextType = AppContext;

    constructor(props) {
      super(props);
      
      this.columns = [
        {
          title: 'Manufacturer',
          dataIndex: 'manufacturer',
          width: '15%',
          editable: true,
        },
        {
          title: 'Device',
          dataIndex: 'device',
          width: '15%',
          editable: true,
        },
        {
            title: 'Our Mono Cartridge Price',
            dataIndex: 'mono_price',
            responsive: ['md'],
        },
        {
          title: 'Our Color Price',
          dataIndex: 'color_price',
          responsive: ['md'],
        },
        {
            title: 'Your Savings',
            dataIndex: 'savings',
            responsive: ['md'],
        },
        {
            title: 'Retail Mono Cartridge Price',
            dataIndex: 'retail_mono_price',
            responsive: ['lg'],
        },
        {
            title: 'Retail Color Cartridge Price',
            dataIndex: 'retail_color_price',
            responsive: ['lg'],
        },
        {
          title: 'operation',
          dataIndex: 'operation',
          render: (_, record) =>
            this.state.dataSource.length >= 1 ? (
              <Popconfirm title="Sure to delete?" onConfirm={() => this.handleDelete(record.key)}>
                <a>Delete</a>
              </Popconfirm>
            ) : null,
        },
      ];

      this.state = {
        dataSource: [
          {
            key: 0,
            manufacturer: 'Select...',
            device: 'Select...',
            mono_price: '$0.00',
            color_price: '$0.00',
            savings: '$0.00',
            retail_color_price: '$0.00',
            retail_mono_price: '$0.00',
            details: ''
          }
        ],
        count: 1,
      };
    }
  
    componentDidMount() {
      const { purchased } = this.context;
      document.getElementById('rev').click();
    };

    
    
    expandedRowRenderer = (record) => {
      const { selectVariant } = this.context;
      
      const rowSelection = {
        onChange: (selectedRowKeys, selectedRows) => {
          selectVariant(selectedRowKeys)
          // console.log(`selectedRowKeys: ${selectedRowKeys}`, 'selectedRows: ', selectedRows);
        },
        onSelect: (record, selected, selectedRows) => {
          // console.log(record, selected, selectedRows);
        },
        onSelectAll: (selected, selectedRows, changeRows) => {
          // console.log(selected, selectedRows, changeRows);
        },
      };

      const columns = [
        {title: 'Model name', dataIndex: 'model_name', key: 'model_name'},
        {title: 'Out Cost', dataIndex: 'outCost', key: 'outCost'},
        {title: 'MSRP', dataIndex: 'msrp', key: 'msrp'},
        {title: 'Care Pack Cost', dataIndex: 'carePackCost', key: 'carePackCost'}
      ]
    
      const variants = record.details.printer_costs;
      const data = [];
      
      const addData = (item, key) => (data.push({
        key: key,
        model_name: item.model_name,
        outCost: item.outCost,
        msrp: item.msrp,
        carePackCost: item.carePackCost
      }));
    
      forEachObjIndexed(addData, variants);
     
      
      return  <Table columns={columns} dataSource={data} pagination={false} rowSelection={{ ...rowSelection }} />
             
    }

    handleDelete = (key) => {
      const dataSource = [...this.state.dataSource];
      this.setState({
        dataSource: dataSource.filter((item) => item.key !== key),
      });
    };
    handleAdd = () => {
      const { count, dataSource } = this.state;
      const { resetDeviceDetails } = this.context;

      resetDeviceDetails()
      const newData = {
        key: count,
        manufacturer: 'Select...',
        device: 'Select...',
        mono_price: '$0.00',
        color_price: '$0.00',
        savings: '$0.00',
        retail_color_price: '$0.00',
        retail_mono_price: '$0.00',
        details: ''
      };
      
      this.setState({
        dataSource: [...dataSource, newData],
        count: count + 1,
      });
    };
    handleSave = (row) => {
      const newData = [...this.state.dataSource];
      const index = newData.findIndex((item) => row.key === item.key);
      const item = newData[index];
      newData.splice(index, 1, { ...item, ...row });
      this.setState({
        dataSource: newData,
      });
    };

    Submit = (data) => {
      const { sendProposedPurchase, variants } = this.context; 
      sendProposedPurchase(data, variants);
    };

    render() {
      const { dataSource } = this.state;
      const components = {
        body: {
          row: EditableRow,
          cell: EditableCell,
        }, 

      };
      const columns = this.columns.map((col) => {
        if (!col.editable) {
          return col;
        }
  
        return {
          ...col,
          onCell: (record) => 
          {
            const { details, recordIdx } = this.context;
            // set default to zero for negative savings.
            const getSavings = (dets) => {
              const val = +((dets.printer_details.retail_mono) - (dets.ppc_mono)) + ((dets.printer_details.retail_color) - (dets.ppc_color))
              return (val >= 0) ? val : 0; 
            }
            // display calculated data in record row cells.
            if(record.key === recordIdx) {
              record.savings = !isNil(details) ? '$'+ getSavings(details).toFixed(2) : '$0.00';
              record.retail_mono_price = !isNil(details) ? '$'+Number.parseFloat(details.printer_details.retail_mono).toFixed(2) : '$0.00';
              record.retail_color_price = !isNil(details) ? '$'+Number.parseFloat(details.printer_details.retail_color).toFixed(2) : '$0.00';
              record.mono_price=!isNil(details) ? '$'+Number.parseFloat(details.ppc_mono).toFixed(2) : '$0.00';
              record.color_price=!isNil(details) ? '$'+Number.parseFloat(details.ppc_color).toFixed(2) : '$0.00';
              record.details = !isNil(details) ? details : ''
            }
            

            return {
                    record,
                    editable: col.editable,
                    dataIndex: col.dataIndex,
                    title: col.title,
                    handleSave: this.handleSave,
                  }
          },
        };
      });
      return (
        <div >
          <Button
            onClick={this.handleAdd}
            type="primary"
            style={{
              marginBottom: 16,
            }}
          >
            Add a row
          </Button>
          <Table
            components={components}
            rowClassName={() => 'editable-row'}
            bordered
            dataSource={dataSource}
            columns={columns}
            expandable={{
              rowExpandable: (record) => (length(keys(record.details.printer_costs))),
              expandedRowRender: (record) => (this.expandedRowRenderer(record)) 
            }}
            
          />
          <Button
            onClick={() => {this.Submit(dataSource)}}
            type="primary"
            style={{
              marginRight: '15px',
              marginBottom: 16,
            }}
          >
            Submit
          </Button>
          <Button
            onClick={() => { 
              this.context.systemReset();
              document.getElementById('start').click();
            }}
            type="primary"
            style={{
              marginBottom: 16,
            }}
          >
            Reset
          </Button>
        </div>
        
      );
    }
  }
  
export default EditableTable; 